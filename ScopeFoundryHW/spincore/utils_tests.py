from utils.plotting import test_plotting
from utils.printing import print_flags
from utils.short_pulse_feature import test_short_pulse_feature

if __name__ == "__main__":
    print_flags(2**13 ^ 2**15)
    print_flags(1 << 13 ^ 1 << 15)
    test_plotting()
    test_short_pulse_feature()
