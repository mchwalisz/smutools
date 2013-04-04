
import os
env = Environment(ENV=os.environ)

def pyuic4_build(target, source, env):
    action='pyuic4 source -o target'


uic_builder_py = Builder(
    action="pyside-uic $SOURCE > $TARGET",  # | sed 's/from qwt_plot import QwtPlot/from PyQt4.Qwt5 import QwtPlot/'
    suffix='.py',
    src_suffix='.ui',
    single_source=True)
env.Append(BUILDERS={'FormPy': uic_builder_py})

env.FormPy(target='MonitorMainUI.py', source=['MonitorMainUI.ui'])
