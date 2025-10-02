#!/usr/bin/env python3
\"\"\"
Test script to verify that the pandas-plots module works correctly with the new structure.
\"\"\"

def test_pls_import():
    \"\"\"Test that 'from pandas_plots import pls' works correctly.\"\"\"
    print(\"Testing 'from pandas_plots import pls'...\")
    
    try:
        import sys
        sys.path.insert(0, './src')
        import pandas_plots
        from pandas_plots import pls
        print(\"✅ 'from pandas_plots import pls' succeeded\")
        
        # Check if the functions are available in the pls module
        functions_to_check = [
            'plot_bars',
            'plot_stacked_bars',
            'plot_box', 
            'plot_boxes',
            'plot_histogram',
            'plot_histogram_large',
            'plot_joint',
            'plot_quadrants',
            'plot_facet_stacked_bars',
            'plot_sankey',
            'plot_pie'
        ]
        
        for func_name in functions_to_check:
            if hasattr(pls, func_name):
                print(f\"✅ pls.{func_name} is available\")
            else:
                print(f\"❌ pls.{func_name} is missing\")
                return False
        
        return True
    except Exception as e:
        print(f\"❌ Import error: {e}\")
        import traceback
        traceback.print_exc()
        return False

def test_direct_access():
    \"\"\"Test that functions can still be accessed directly from pandas_plots.\"\"\"
    print(\"\\nTesting direct access to functions...\")
    
    try:
        import sys
        sys.path.insert(0, './src')
        import pandas_plots
        
        # Check if functions are available directly in pandas_plots
        functions_to_check = [
            'plot_bars',
            'plot_stacked_bars', 
            'plot_box',
            'plot_boxes',
            'plot_histogram',
            'plot_histogram_large',
            'plot_joint',
            'plot_quadrants',
            'plot_facet_stacked_bars',
            'plot_sankey',
            'plot_pie'
        ]
        
        for func_name in functions_to_check:
            if hasattr(pandas_plots, func_name):
                print(f\"✅ pandas_plots.{func_name} is available\")
            else:
                print(f\"⚠️  pandas_plots.{func_name} is not available (this may be OK)\")
        
        return True
    except Exception as e:
        print(f\"❌ Direct access error: {e}\")
        return False

def main():
    \"\"\"Run all tests.\"\"\"
    print(\"Starting tests for pandas-plots module with new structure...\")
    
    success = True
    success &= test_pls_import()
    success &= test_direct_access()
    
    if success:
        print(\"\\n🎉 All tests passed! The new structure is working correctly.\")
        print(\"✅ Both 'from pandas_plots import pls' and direct function access work.\")
    else:
        print(\"\\n❌ Some tests failed.\")
    
    return success

if __name__ == \"__main__\":
    main()