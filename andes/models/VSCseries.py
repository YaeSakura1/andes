"""Voltage-source converter models"""

from andes.models.dcbase import ACDC2Term, ACDC3Term
from andes.core.param import NumParam
from andes.core.var import Algeb, State, ExtState, ExtAlgeb  # NOQA
from andes.core.service import ConstService, ExtService  # NOQA
from andes.core.discrete import HardLimiter, Switcher  # NOQA


class VSCSeries(ACDC2Term):
    """Data for VSC series in power flow"""
    def __init__(self, system, config):
        ACDC2Term.__init__(self, system, config)
        self.rse = NumParam(default=0.0025, info="AC interface resistance", unit="ohm", z=True,
                            tex_name='r_{se}')
        self.xse = NumParam(default=0.06, info="AC interface reactance", unit="ohm", z=True,
                            tex_name='x_{se}')

        self.control = NumParam(info="Control method: 0-PQ, 1-PV, 2-vQ or 3-vV", mandatory=True)
        self.v0 = NumParam(default=1.0, info="AC voltage setting (PV or vV) or initial guess (PQ or vQ)")
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

        self.vsemax = NumParam(default=1.1, info="Maximum ac interface voltage", unit="pu")
        self.vsemin = NumParam(default=0.9, info="Minimum ac interface voltage", unit="pu")
        self.Isemax = NumParam(default=2, info="Maximum ac current", unit="pu")

        # define variables and equations
        self.flags.update({'pflow': True})
        self.flags.update({'tds': True})
        self.group = 'StaticACDC'

        self.gse = ConstService(tex_name='g_{se}', v_str='re(1/(rse + 1j * xse))', vtype=complex)
        self.bse = ConstService(tex_name='b_{se}', v_str='im(1/(rse + 1j * xse))', vtype=complex)

        self.mode = Switcher(u=self.control, options=(0, 1, 2, 3))

        self.ase = Algeb(info='voltage phase behind the transformer',
                         unit='rad',
                         tex_name=r'\theta_{sh}',
                         v_str='a',
                         e_str='u * (gse * v**2 - gse * vh * vk * cos(a - b) - '
                               'bse * vh * vk * sin(a - b) - '
                               'gse * vh * vse * cos(a - ase) - '
                               'bse * vh * vse * sin(a - ase)) - pse',
                         diag_eps=True,
                         )
        self.vse = Algeb(info='voltage magnitude behind transformer',
                         tex_name="V_{sh}",
                         unit='p.u.',
                         v_str='v0',
                         e_str='u * (-bse * vh**2 - gse * vh * vk * sin(a - b) + '
                               'bse * vh * vk * cos(a - b) - '
                               'gse * vh * vse * sin(a - ase) + '
                               'bse * vh * vse * cos(a - ase)) - qse',
                         diag_eps=True,
                         )
        self.ask = Algeb(info='voltage phase behind the transformer',
                         unit='rad',
                         tex_name=r'\theta_{sk}',
                         v_str='b',
                         e_str='u * (gse * v**2 - gse * v * vsh * cos(a - b) - '
                               'bse * v * vsh * sin(a - b) + '
                               'gse * v * vsh * cos(a - ase) - '
                               'bse * v * vsh * sin(a - ase)) - pse',
                         diag_eps=True,
                         )
        self.vsk = Algeb(info='voltage magnitude behind transformer',
                         tex_name="V_{sk}",
                         unit='p.u.',
                         v_str='v0',
                         e_str='u * (-bse * v**2 - gse * v * vse * sin(a - b) + '
                               'bse * v * vse * cos(a - b) - '
                               'gse * v * vse * sin(a - ase) + '
                               'bse * v * vse * cos(a - ase)) - qse',
                         diag_eps=True,
                         )
        self.pse = Algeb(info='active power injection into VSC',
                         tex_name="P_{se}",
                         unit='p.u.',
                         v_str='p0 * (mode_s0 + mode_s1)',
                         e_str='u * (mode_s0 + mode_s1) * (p0 - pse) + '
                               'u * (mode_s2 + mode_s3) * (v1 - v2 - vdc0)',
                         diag_eps=True,
                         )
        self.qse = Algeb(info='reactive power injection into VSC',
                         tex_name="Q_{se}",
                         v_str='q0 * (mode_s0 + mode_s2)',
                         e_str='u * (mode_s0 + mode_s2) * (q0 - qse) + '
                               'u * (mode_s1 + mode_s3) * (v0 - v)',
                         diag_eps=True,
                         )
        self.pdc = Algeb(info='DC power injection',
                         tex_name="P_{dc}",
                         v_str='0',
                         e_str='u * (gse * vse * vse - gse * v * vse * cos(a - ase) + '
                               'bse * v * vse * sin(a - ase)) + pdc',
                         )
        self.a.e_str = '-pse'
        self.v.e_str = '-qse'
        self.v1.e_str = '-pdc / (v1 - v2)'
        self.v2.e_str = 'pdc / (v1 - v2)'