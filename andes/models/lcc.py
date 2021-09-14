"""line commutated converter models"""

from andes.models.dcbase import ACDC2Term
from andes.core.param import NumParam
from andes.core.var import Algeb, State, ExtState, ExtAlgeb  # NOQA
from andes.core.service import ConstService, ExtService  # NOQA
from andes.core.discrete import HardLimiter, Switcher, AntiWindup  # NOQA
from andes.core.block import PIController  #NOQA
import math
pi=math.pi

class LCC(ACDC2Term):
    """Data for LCC in power flow"""
    def __init__(self, system, config):
        ACDC2Term.__init__(self, system, config)
        self.rsh = NumParam(default=0.0025, info="AC interface resistance", unit="ohm", z=True,
                            tex_name='r_{sh}')
        self.xsh = NumParam(default=0.06, info="AC interface reactance", unit="ohm", z=True,
                            tex_name='x_{sh}')

        self.p0 = NumParam(default=0.0, info="AC active power setting", unit="pu")
        self.q0 = NumParam(default=0.0, info="AC reactive power setting", unit="pu")
        self.vdc0 = NumParam(default=1.0, info="DC voltage setting", unit="pu", tex_name='v_{dc0}')

        self.k0 = NumParam(default=0.0, info="Loss coefficient - constant")
        self.k1 = NumParam(default=0.0, info="Loss coefficient - linear")
        self.k2 = NumParam(default=0.0, info="Loss coefficient - quadratic")

        self.droop = NumParam(default=0.0, info="Enable dc voltage droop control", unit="boolean")
        self.K = NumParam(default=0.0, info="Droop coefficient")
        self.vhigh = NumParam(default=9999, info="Upper voltage threshold in droop control", unit="pu")
        self.vlow = NumParam(default=0.0, info="Lower voltage threshold in droop control", unit="pu")

        self.vshmax = NumParam(default=1.1, info="Maximum ac interface voltage", unit="pu")
        self.vshmin = NumParam(default=0.9, info="Minimum ac interface voltage", unit="pu")
        self.Ishmax = NumParam(default=2, info="Maximum ac current", unit="pu")

        self.KR = NumParam(default=1, info="Rectifier-side transformer tap ratio", unit="pu/pu")
        self.KI = NumParam(default=1, info="Inverter-side transformer tap ratio", unit="pu/pu")

        self.amax = NumParam(default=100, info="Maximum firing angle", unit="rad")
        self.amin = NumParam(default=5, info="Minimum firing angle", unit="rad")
        self.bmax = NumParam(default=60, info="Maximum extinction angle", unit="rad")
        self.bmin = NumParam(default=15, info="Minimum extinction angle", unit="rad")

        self.XRc = NumParam(default=0.03, info="Commutation reactance", unit="pu")
        self.kr = NumParam(default=0.995, info="consider the commutation effect")
        self.N = NumParam(default=6, info="the converter bridge number")
        self.d = NumParam(default=0.436, info="the converter power factor angle", unit="rad")

        self.ids = NumParam(default=2, info="the current set value", unit="pu")
        self.vds = NumParam(default=1, info="the voltage set value", unit="pu")
        self.pds = NumParam(default=2, info="the power set value", unit="pu")
        self.ads = NumParam(default=18, info="the firing angles set value", unit="rad")
        self.bds = NumParam(default=22, info="the extinct angles set value", unit="rad")
        self.kds = NumParam(default=1, info="the ratios set value", unit="pu")

        self.control = NumParam(info="Control method: 0-CC, 1-CV, 2-CP, 3-CIA, 4-CEA, or 5-CR", mandatory=True)

        # define variables and equations
        self.flags.update({'pflow': True})
        self.flags.update({'tds': True})
        self.group = 'staticACDC'

        self.mode = Switcher(u=self.control, options=(0, 1, 2, 3, 4, 5))

        self.ar = Algeb(info='Rectifier firing angle',
                        unit='rad',
                        tex_name='theta_{h}',
                        v_str='ar',
                        e_str='',
                        diag_eps=True,
                        )
        self.bi = Algeb(info='Inverter extinction angle',
                        unit='rad',
                        tex_name='theta_{h}',
                        v_str='bi',
                        e_str='',
                        diag_eps=True,
                        )

# 补充方程
# (1)换流器方程:
# 整流侧
        self.vdr = Algeb(info='the rectifier dc power equations at ac side',
                         unit='p.u.',
                         v_str='vdr',
                         e_str='3 * 2**0.5/pi * N * KR * v * cos(ar) - 3/pi * N * XRc * Id - vdr',
                         diag_eps=True,
                         )
        self.vdr = Algeb(info='the relationship between DC voltage and AC voltage',
                         unit='p.u.',
                         v_str='vdr',
                         e_str='kr * 3 * 2**0.5/pi * N * KR * v * cos(d) - vdr',
                         diag_eps=True,
                         )
        self.Pdr = Algeb(info='the rectifier active power',
                         unit='p.u.',
                         v_str='pdr',
                         e_str='vd * Id',
                         diag_eps=True,
                         )
        self.Qdr = Algeb(info='the rectifier reactive power',
                         unit='p.u.',
                         v_str='qdr',
                         e_str='vd * Id * (-1) * tan(d)',
                         diag_eps=True,
                         )

# 逆变侧
        self.vdi = Algeb(info='the inverter dc power equations at ac side',
                         unit='p.u.',
                         v_str='vdi',
                         e_str='3 * 2**0.5/pi * N * KI * v * cos(bi) - 3/pi * N * XRc * Id - vdi',
                         diag_eps=True,
                         )
        self.vdi = Algeb(info='the relationship between DC voltage and AC voltage',
                         unit='p.u.',
                         v_str='vdi',
                         e_str='kr * 3 * 2**0.5/pi * N * KI * v * cos(d) - vdi',
                         diag_eps=True,
                         )
        self.Pdi = Algeb(info='the inverter active power',
                         unit='p.u.',
                         v_str='pdi',
                         e_str='vdi * Id',
                         diag_eps=True,
                         )
        self.Qdi = Algeb(info='the inverter reactive power',
                         unit='p.u.',
                         v_str='qdi',
                         e_str='vd * Id * (-1) * tan(d)',
                         diag_eps=True,
                         )

# 换流器损耗
        self.ic = Algeb(info='the fundamental current injected into the converter',
                        unit='p.u.',
                        v_str='ic',
                        e_str='6 * 2**0.5/pi * kr * N * Id',
                        diag_eps=True,
                        )
        self.ploss = Algeb(info='the lcc converter loss',
                           unit='p.u.',
                           v_str='ploss',
                           e_str='k2 * ic**2 + k1 * ic + k0',
                           diag_eps=True,
                           )
        self.Psr = Algeb(info='the apparent active power at rectifier side injected from the ac grid to the lcc',
                         unit='p.u.',
                         v_str='psr',
                         e_str='pdr + ploss',
                         diag_eps=True,
                         )
        self.Qsr = Algeb(info='the apparent reactive power at rectifier side injected from the ac grid to the lcc',
                         unit='p.u.',
                         v_str='qsr',
                         e_str='psr * (-1) * tan(d)',
                         diag_eps=True,
                         )
        self.Psi = Algeb(info='the apparent active power at inverter side injected from the ac grid to the lcc',
                         unit='p.u.',
                         v_str='psi',
                         e_str='pdi + ploss',
                         diag_eps=True,
                         )
        self.Qsi = Algeb(info='the apparent reactive power at inverter side injected from the ac grid to the lcc',
                         unit='p.u.',
                         v_str='qsi',
                         e_str='psi * (-1) * tan(d)',
                         diag_eps=True,
                         )


# (2)直流网络方程：直流系统网络方程即为直流输电线路的数学方程
#       采用电阻电路
        self.ldc = Algeb(info='dc net equation',
                         unit='p.u.',
                         v_str='ldc',
                         e_str='vdr - vdi - R * Id',
                         diag_eps=True,
                         )


# (3)控制方程:
        self.CC = Algeb(info='constant current control',
                        unit='p.u.',
                        v_str='cc',
                        e_str='Id - ids',
                        diag_eps=True,
                        )
        self.CV = Algeb(info='constant voltage control',
                        unit='p.u.',
                        v_str='cv',
                        e_str='vd - vds',
                        diag_eps=True,
                        )
        self.CP = Algeb(info='constant power control',
                        unit='p.u.',
                        v_str='cp',
                        e_str='vd * Id - pds',
                        diag_eps=True,
                        )
        self.CIA = Algeb(info='constant firing angle control',
                         unit='raf',
                         v_str='cia',
                         e_str='cos(ar) - cos(ads)',
                         diag_eps=True,
                         )
        self.CEA = Algeb(info='constant extinction angle control',
                         unit='rad',
                         v_str='cea',
                         e_str='cos(bi) - cos(bds)',
                         diag_eps=True,
                         )
        self.CR = Algeb(info='constant ratios control',
                        unit='p.u.',
                        v_str='cr',
                        e_str='KR - kds',
                        diag_eps=True,
                        )

# ---------------------------------------------------------------------------------------------------------------

        # self.ash = Algeb(info='voltage phase behind the transformer',
        #                  unit='rad',
        #                  tex_name=r'\theta_{sh}',
        #                  v_str='a',
        #                  e_str='u * (gsh * v**2 - gsh * v * vsh * cos(a - ash) - '
        #                        'bsh * v * vsh * sin(a - ash)) - psh',
        #                  diag_eps=True,
        #                  )
        # self.vsh = Algeb(info='voltage magnitude behind transformer',
        #                  tex_name="V_{sh}",
        #                  unit='p.u.',
        #                  v_str='v0',
        #                  e_str='u * (-bsh * v**2 - gsh * v * vsh * sin(a - ash) + '
        #                        'bsh * v * vsh * cos(a - ash)) - qsh',
        #                  diag_eps=True,
        #                  )
        # self.psh = Algeb(info='active power injection into VSC',
        #                  tex_name="P_{sh}",
        #                  unit='p.u.',
        #                  v_str='p0 * (mode_s0 + mode_s1)',
        #                  e_str='u * (mode_s0 + mode_s1) * (p0 - psh) + '
        #                        'u * (mode_s2 + mode_s3) * (v1 - v2 - vdc0)',
        #                  diag_eps=True,
        #                  )
        # self.qsh = Algeb(info='reactive power injection into VSC',
        #                  tex_name="Q_{sh}",
        #                  v_str='q0 * (mode_s0 + mode_s2)',
        #                  e_str='u * (mode_s0 + mode_s2) * (q0 - qsh) + '
        #                        'u * (mode_s1 + mode_s3) * (v0 - v)',
        #                  diag_eps=True,
        #                  )
        # self.pdc = Algeb(info='DC power injection',
        #                  tex_name="P_{dc}",
        #                  v_str='0',
        #                  e_str='u * (gsh * vsh * vsh - gsh * v * vsh * cos(a - ash) + '
        #                        'bsh * v * vsh * sin(a - ash)) + pdc',
        #                  )
        # self.a.e_str = '-psh'
        # self.v.e_str = '-qsh'
        # self.v1.e_str = '-pdc / (v1 - v2)'
        # self.v2.e_str = 'pdc / (v1 - v2)'

