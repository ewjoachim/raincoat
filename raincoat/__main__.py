from . import main


# What would one do for 100% coverage...
def launch(name):
    if name == '__main__':
        main()  # pylint: disable=no-value-for-parameter


launch(__name__)
