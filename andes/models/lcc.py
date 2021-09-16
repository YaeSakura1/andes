"""line commutated converter models"""

from andes.models.dcbase import ACDC2Term
from andes.core.param import NumParam
from andes.core.var import Algeb, State, ExtState, ExtAlgeb  # NOQA
from andes.core.service import ConstService, ExtService  # NOQA
from andes.core.discrete import HardLimiter, Switcher, AntiWindup  # NOQA
from andes.core.block import PIController  #NOQA

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

        self.Xc = NumParam(default=0.03, info="Commutation reactance", unit="pu")
        self.kr = NumParam(default=0.995, info="consider the commutation effect")
        self.N = NumParam(default=6, info="the converter bridge number")
        self.d = NumParam(default=0.436, info="the converter power factor angle", unit="rad")

        self.ids = NumParam(default=2, info="the current set value", unit="pu")
        self.vds = NumParam(default=1, info="the voltage set value", unit="pu")
        self.pds = NumParam(default=2, info="the power set value", unit="pu")
        self.ads = NumParam(default=18, info="the firing angles set value", unit="rad")
        self.bds = NumParam(default=22, info="the extinct angles set value", unit="rad")
        self.kds = NumParam(default=1, info="the ratios set value", unit="pu")

        self.ar = NumParam(default=15, info="firing delay angle", unit="rad")
        self.bi = NumParam(default=15, info="extinction advance angle", unit="rad")

        self.idr = NumParam(default=1)
        self.idi = NumParam(default=1)
        self.R = NumParam(default=3.6)

        self.control = NumParam(info="Control method: 0-CC, 1-CV, 2-CP, 3-CIA, 4-CEA, or 5-CR", mandatory=True)

        # define variables and equations
        self.flags.update({'pflow': True})
        self.flags.update({'tds': True})
        self.group = 'StaticACDC'

        self.mode = Switcher(u=self.control, options=(0, 1, 2, 3, 4, 5))


# 整流器方程
        self.vd0r = Algeb(info='ideal no-load direct voltage',
                          unit='p.u.',
                          tex_name='V_{d0r}',
                          v_str='vd0r',
                          e_str='3 * 2**0.5/pi * KR * N * v - vd0r',
                          diag_eps=True,
                          )
        self.vdr = Algeb(info='rectifier dc voltage',
                         unit='p.u.',
                         tex_name='V_{dr}',
                         v_str='vdr',
                         e_str='3 * 2**0.5/pi * KR * N * v * cos(ar)- 3/pi * N * Xc * idr - vdr',
                         diag_eps=True,
                         )
        self.pr = Algeb(info='rectifier active power',
                        unit='p.u.',
                        tex_name='P_{r}',
                        v_str='pr',
                        e_str='vdr * idr - pr',
                        diag_eps=True,
                        )
        self.qr = Algeb(info='rectifier reactive power',
                        unit='p.u.',
                        tex_name='Q_{r}',
                        v_str='qr',
                        e_str='(vdr * idr) * tan(dr) - qr',
                        diag_eps=True,
                        )
        self.dr = Algeb(info='the phase angle between the ac voltage and fundamental current',
                        unit='p.u.',
                        tex_name=r'\phi_{r}',
                        v_str='dr',
                        e_str='acos(vdr/vd0r) - dr',
                        diag_eps=True,
                        )
# 逆变器方程
        self.vd0i = Algeb(info='ideal no-load direct voltage',
                          unit='p.u.',
                          tex_name='V_{d0i}',
                          v_str='vd0r',
                          e_str='3 * 2**0.5/pi * KR * N * v - vd0i',
                          diag_eps=True,
                          )
        self.vdi = Algeb(info='inverter dc voltage',
                         unit='p.u.',
                         tex_name='V_{di}',
                         v_str='vdi',
                         e_str='3 * 2**0.5/pi * KR * N * v * cos(bi)- 3/pi * N * Xc * idi - vdi',
                         diag_eps=True,
                         )
        self.pi = Algeb(info='inverter active power',
                        unit='p.u.',
                        tex_name='P_{i}',
                        v_str='pi',
                        e_str='vdi * idi - pi',
                        diag_eps=True,
                        )
        self.qi = Algeb(info='inverter reactive power',
                        unit='p.u.',
                        tex_name='Q_{i}',
                        v_str='qi',
                        e_str='(vdi * idi) * tan(di) - qi',
                        diag_eps=True,
                        )
        self.di = Algeb(info='the phase angle between the ac voltage and fundamental current',
                        unit='p.u.',
                        tex_name=r'\phi_{i}',
                        v_str='di',
                        e_str='acos(vdi/vd0i) - di',
                        diag_eps=True,
                        )

# 线路方程
        self.id = Algeb(info='dc current',
                        unit='p.u.',
                        tex_name='I_{d}',
                        v_str='id',
                        e_str='vdi + R * id - vdr',
                        diag_eps=True,
                        )
# 控制方程:
        self.CC = Algeb(info='constant current control',
                        unit='p.u.',
                        v_str='CC',
                        e_str='id - ids',
                        diag_eps=True,
                        )
        self.CV = Algeb(info='constant voltage control',
                        unit='p.u.',
                        v_str='CV',
                        e_str='id - vds',
                        diag_eps=True,
                        )
        self.CP = Algeb(info='constant power control',
                        unit='p.u.',
                        v_str='CP',
                        e_str='id * id - pds',
                        diag_eps=True,
                        )
        self.CIA = Algeb(info='constant firing angle control',
                         unit='raf',
                         v_str='CIA',
                         e_str='cos(ar) - cos(ads)',
                         diag_eps=True,
                         )
        self.CEA = Algeb(info='constant extinction angle control',
                         unit='rad',
                         v_str='CEA',
                         e_str='cos(bi) - cos(bds)',
                         diag_eps=True,
                         )
        self.CR = Algeb(info='constant ratios control',
                        unit='p.u.',
                        v_str='CR',
                        e_str='KR - kds',
                        diag_eps=True,
                        )