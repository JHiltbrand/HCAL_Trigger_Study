#!/usr/bin/env python

# Map event record number in the PU TTree to entry number in the NOPU TTree since the two TTrees are not necessarrily in the same order...
PU2NOPUMAP = {
    # Remove before flight
    # To be copied from makeEventMap.py output
    
    # Example format
    # 2903 : 1, 2904 : 0, 2901 : 3, 2902 : 2, 2905 : 4, 2907 : 5, 2909 : 6, 2906 : 7, 2908 : 9, 
    # 2911 : 8, 2912 : 10, 2913 : 11, 2916 : 12, 2914 : 13, 2910 : 14, 2917 : 15, 2915 : 16, 2918 : 17,
    # 2919 : 18, 2921 : 19, 2924 : 20, 2922 : 21, 2926 : 22, 2920 : 23, 2927 : 24, 2923 : 26, 2925 : 25,
    # 2928 : 27, 2932 : 28, 2933 : 29, 2929 : 31, 2930 : 30, 2934 : 32, 2937 : 33, 2936 : 34, 2939 : 35
}
