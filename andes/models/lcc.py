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

        self.MR = NumParam(default=1, info="Rectifier-side transformer tap ratio", unit="pu/pu")
        self.MI = NumParam(default=1, info="Inverter-side transformer tap ratio", unit="pu/pu")




        # define variables and equations
        self.flags.update({'pflow':True})
        self.group = 'staticACDC'

        self.vh = Algeb(info='voltage magnitude behind rectifer transformer',
                        unit='pu',
                        tex_name="V_{h}",
                        v_str='vh',
                        e_str='',
                        diag_eps=True,
                        )
        self.vk = Algeb(info='voltage magnitude behind inverter transformer',
                        unit='pu',
                        tex_name="V_{h}",
                        v_str='vk',
                        e_str='',
                        diag_eps=True,
                        )
        self.α = Algeb(info="Rectifier firing angle",
                       unit='rad',
                       tex_name='theta_{h}',
                       v_str='',
                       e_str='',
                       diag_eps=True,
                       )
        self.γ = Algeb(info='Inverter extinction angle',
                       unit='rad',
                       tex_name='theta_{h}',
                       v_str='',
                       e_str='',
                       diag_eps=True,
                       )
        self.θh = Algeb(info="angle between the average ac voltage and the ac current of the retifier",
                        unit='rad',
                        tex_name='theta_{sh}',
                        v_str='',
                        e_str='',
                        diag_eps=True,
                        )
        self.θk = Algeb(info="angle between the average ac voltage and the ac current of the inverter",
                        unit='rad',
                        tex_name='theta_{sh}',
                        v_str='',
                        e_str='',
                        diag_eps=True,
                        )
        self.ph = Algeb(info='active power injection into LCC',
                        tex_name="P_{h}",
                        unit='p.u.',
                        v_str='ph',
                        e_str='u * (-vrdc * irdc)',
                        diag_eps=True,
                        )
        self.qh = Algeb(info='reactive power injection into LCC',
                        unit="p.u.",
                        tex_name="Q_{h}",
                        v_str='qh',
                        e_str='u * (-0.9995 * 3**0.5/3.1415) * MR * vh * irdc * sin(θh)',
                        diag_eps=True,
                        )
        self.pk = Algeb(info='the interver injects active power',
                        unit='p.u.',
                        v_str='pk',
                        e_str='u * ( - vidc * iidc)',
                        diag_eps=True,
                        )
        self.qk = Algeb(info='consumes reactive power at the ac bus',
                        unit='p.u.',
                        v_str='qk',
                        e_str='u * ( -0.9995 * 3**0.5/3.1415) * MI * vk * iidc * sin(θk)',
                        diag_eps=True,
                        )