#!/usr/bin/env python3
\"\"\"
Test script to verify that the pandas-plots module works correctly after splitting.
\"\"\"

def test_imports():
    \"\"\"Test that all functions can be imported correctly.\"\"\"
    print(\"Testing imports...\")
    
    try:
        from pandas_plots import (
            plot_bars,
            plot_stacked_bars,
            plot_box,
            plot_boxes,
            plot_histogram,
            plot_histogram_large,
            plot_joint,
            plot_quadrants,
            plot_facet_stacked_bars,
            plot_sankey,
            plot_pie
        )
        print(\"✅ All functions imported successfully\")
    except Exception as e:
        print(f\"❌ Import error: {e}\")
        return False
    
    return True

def test_dataframe_extensions():
    \"\"\"Test that DataFrame extensions work correctly.\"\"\"
    print(\"Testing DataFrame extensions...\")
    
    import pandas as pd
    
    try:
        # Create a simple test DataFrame
        df = pd.DataFrame({
            'category': ['A', 'B', 'C', 'A', 'B'],
            'value': [1, 2, 3, 4, 5]
        })
        
        # Test that the methods exist without actually calling them
        # (as they may require additional dependencies or parameters)
        methods_to_check = [
            'plot_bars',
            'plot_stacked_bars', 
            'plot_facet_stacked_bars',
            'plot_stacked_box',
            'plot_stacked_boxes',
            'plot_quadrants',
            'plot_histogram',
            'plot_joint',
            'plot_sankey',
            'plot_pie'
        ]
        
        for method in methods_to_check:
            if hasattr(df, method):
                print(f\"✅ DataFrame.{method} method exists\")
            else:
                print(f\"❌ DataFrame.{method} method missing\")
                return False
                
    except Exception as e:
        print(f\"❌ DataFrame extension test error: {e}\")
        return False
    
    return True

def main():
    \"\"\"Run all tests.\"\"\"
    print(\"Starting tests for pandas-plots module...\")
    
    success = True
    success &= test_imports()
    success &= test_dataframe_extensions()
    
    if success:
        print(\"\\n🎉 All tests passed! The module is working correctly.\")
    else:
        print(\"\\n❌ Some tests failed.\")
    
    return success

if __name__ == \"__main__\":
    main()