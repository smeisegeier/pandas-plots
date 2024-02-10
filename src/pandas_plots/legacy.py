import warnings
warnings.filterwarnings('ignore')

from scipy import stats
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb

def my_show_info(df, hasPlot=False):
    """show info about given dataframe

    Args:
        df (DataFrame): dataframe
        hasPlot (bool): display plot or not

    Returns:
        DataFrame: self
    """

    df_ = df.copy()
    import io
    # .info(): cleanse whitespaces in column names!
    df_.columns = df_.columns.str.replace(' ', '_')
    buffer = io.StringIO()
    df_.info(buf=buffer)
    
    df_n = df_.select_dtypes(np.number)         # store numeric columns for later
    lines = buffer.getvalue().splitlines()
    df = (pd.DataFrame([x.split() for x in lines[5:-2]], columns=lines[3].split())
        )


    #* .nunique
    uni = df_.nunique().reset_index(drop=True).rename('Uni_Count')


    #* .isnull
    nulls = df_.isnull().sum().reset_index(drop=True).rename('Nulls')
    df = df.join(uni).join(nulls)


    #* .value_count
    mylist = []
    for col in df_.columns:
        # only append if count_values yields a result
        if len(df_[col].value_counts()) > 0:
            line = (
                str(df_[col].value_counts().reset_index().iat[0, 0]) +
                ' | ' +
                str(df_[col].value_counts().reset_index().iat[0, 1])
            )
            mylist.append(line)
    mylist = pd.Series(mylist, name='Most_Frequent')
    df = df.join(mylist)


    #* skew and kurto
    skew = stats.skew(df_n, axis=0, bias=True).round(3)
    skew_t = np.stack((df_n.columns.tolist(),skew), axis=0).T               # stack arrays to have corresponding columns
    skew_tp = pd.DataFrame(skew_t, columns=['var', 'skew'])                 # convert to dataframe, assign column names
    kurto = stats.kurtosis(df_n, axis=0, bias=True).round(3)
    kurto_t = np.stack((df_n.columns.tolist(),kurto), axis=0).T
    kurto_tp = pd.DataFrame(kurto_t, columns=['var', 'kurto'])
    df = df.merge(skew_tp, how='outer', left_on='Column', right_on='var').drop('var', axis=1)   # merge w/ column names
    df = df.merge(kurto_tp, how='outer', left_on='Column', right_on='var').drop('var', axis=1)


    #* .describe
    desc = df_.describe().T.drop(axis=1, columns='count')
    # left outer join on l.Column = r.index
    df = df.merge(desc, how='outer', left_on='Column', right_index=True)


    #* plot
    if hasPlot:
        # PLOT
        # get num columns as list (only to_list() outputs clean strings)
        cols = df.select_dtypes(np.number).columns.to_list()
        # 'Columns' is crucial for the plot - but not numeric :)
        cols.append(df.Column.name)

        # transorm to kvpairs -> auto generate: 'variable' + 'value'
        df_kval = pd.melt(df[cols], id_vars=['Column'])
        # set up facets
        g = sb.FacetGrid(data=df_kval, col_wrap=5,
                        col='variable', sharex=False)
        # x, y may not be named as such ...
        _ = g.map(sb.barplot, 'value', 'Column')

    return df


def my_show_skew_kurto(df, hasPlot = False):
    """return values for skew and kurtosis

    Args:
        df (DataFrame): dataframe
        hasPlot (bool): True if you want to plot the data

    Returns:
        list: list of values for skew and kurtosis
    """

    df_ = df.copy()
    df_ = df_.select_dtypes(np.number)
    _skew = stats.skew(df_, axis=0, bias=True)
    _kurto = stats.kurtosis(df_, axis=0, bias=True)

    # get axis: column-names + skw/kurto columns
    _cols = np.array(df_.columns)
    # stack these into array, then transpose
    _array = np.array([_cols, _skew, _kurto]).T
    # into dataframe, assigen names for new columns
    list_skews = pd.DataFrame(data=_array, columns=[
                            'col', 'skewness', 'kurtosis'])
    
    # PLOT
    if hasPlot:
        _fig, _axs = plt.subplots(1, 2, squeeze=False, figsize=(5, 3))
        _ = sb.barplot(y='col', x='skewness', data=list_skews,
                    orient='horizontal', ax=_axs[0, 0])
        _ = sb.barplot(y='col', x='kurtosis', data=list_skews,
                    orient='horizontal', ax=_axs[0, 1])
    return list_skews



# def describe_df_LEGACY(
#     df: pd.DataFrame,
#     caption: str, 
#     use_plot: bool = True,
#     use_columns: bool = True,
#     renderer: Literal["png", "svg", None] = "png",
#     template: str = os.getenv("THEME_PLOTLY") or "plotly",
#     fig_cols: int = 3,
#     fig_offset: int = None,
#     fig_rowheight: int = 300,
#     sort_mode: Literal["value", "index"] = "value",
# ):
#     """
#     This function takes a pandas DataFrame and a caption as input parameters and prints out the caption as a styled header, followed by the shape of the DataFrame and the list of column names. For each column, it prints out the column name, the number of unique values, and the column data type. If the column is a numeric column with more than 100 unique values, it also prints out the minimum, mean, maximum, and sum values. Otherwise, it prints out the first 100 unique values of the column.

#     Args:
#     df (DataFrame): dataframe
#     caption (str): caption to describe dataframe
#     use_plot (bool): display plot?
#     use_columns (bool): display columns values?
#     renderer (Literal["png", "svg", None]): renderer for plot
#     template (str): template for plotly (see https://plotly.com/python/templates/), default: os.getenv("THEME_PLOTLY") or "plotly"
#     fig_cols (int): number of columns in plot
#     fig_offset (int): offset for plots as iloc Argument. None = no offset, -1 = omit last plot
#     fig_rowheight (int): row height for plot (default 300)
#     sort_mode (Literal["value", "index"]): sort by value or index
    
#     usage:
#     describe_df(
#         df=df,
#         caption="dataframe",
#         use_plot=True,
#         renderer="png",
#         template="plotly",
#         fig_cols=3,
#         fig_offset=None,
#         sort_mode="value",
#     )
    
#     hint: skewness may not properly work if the columns is float and/or has only 1 value
#     """
#     # * check if df is empty
#     if len(df) == 0:
#         print(f"{Style.bold}{Fore.red}DataFrame is empty!{Style.reset}")
#         return
    
#     print(f"{Style.bold}{Fore.red}{'*'*3} {caption} {'*'*3}{Style.reset}")
#     print(f"{Fore.blue}shape: {Style.reset}({df.shape[0]:_}, {df.shape[1]}) {Fore.blue}columns: {Style.reset}{df.columns.tolist()} ")
#     print(f"{Fore.blue}duplicates: {Style.reset}{df.duplicated().sum():_}")

#     # ! old version here
#     # for col in df.columns[:]:
#     #     # * get unique values
#     #     unis = df[col].sort_values().unique()
#     #     header = f"{Fore.yellow}{col}({len(unis):_}|{df[col].dtype}){Style.reset}"
#     #     # * check if num col w/ too many values
#     #     if (df[col].dtype.kind in "biufc") and (len(unis) > 100):
#     #         print(
#     #             f"{header} {Fore.magenta}min:{Style.reset} {df[col].min():_} | {Fore.magenta}median:{Style.reset} {df[col].median().round(2):_}  | {Fore.magenta}mean:{Style.reset} {df[col].mean().round(2):_} | {Fore.magenta}std:{Style.reset} {df[col].std().round(2):_} | {Fore.magenta}cv:{Style.reset} {(df[col].std() / df[col].mean()).round(2):_} | {Fore.magenta}max:{Style.reset} {df[col].max():_} | {Fore.magenta}sum:{Style.reset} {df[col].sum():_}"
#     #         )
#     #     else:
#     #         # * limit output to 100 items
#     #         print(f"{header} {unis[:100]}")

#     def get_uniques_header(col: str):
#         # * get unique values
#         unis = df[col].sort_values().unique()
#         # * get header
#         header = f"{Fore.green}{col}({len(unis):_}|{df[col].dtype}){Style.reset}"
#         return unis, header

#     # * show all columns
#     for col in df.columns[:]:
#         _u, _h = get_uniques_header(col)
#         if use_columns:
#             # * limit output to 100 items
#             print(f"{_h} {_u[:100]}")
#         else:
#             print(f"{_h}")

#     print(f"{'*'*3}")
#     # * only show numerics
#     for col in df.select_dtypes('number').columns:
#         _u, _h = get_uniques_header(col)

#         print(
#             f"{_h} {Fore.magenta}min:{Style.reset} {round(df[col].min(),3):_} | {Fore.magenta}max:{Style.reset} {round(df[col].max(),3):_} | {Fore.magenta}median:{Style.reset} {round(df[col].median(),3):_} | {Fore.magenta}mean:{Style.reset} {round(df[col].mean(),3):_} | {Fore.magenta}std:{Style.reset} {round(df[col].std(),3):_} | {Fore.magenta}cv:{Style.reset} {df[col].std() / round(df[col].mean(),3):_} | {Fore.magenta}sum:{Style.reset} {round(df[col].sum(),3):_} | {Fore.magenta}skew:{Style.reset} {round(stats.skew(df[col]),3)} | {Fore.magenta}kurto:{Style.reset} {round(stats.kurtosis(df[col]),3)}"
#         )

#     # * show missings
#     print(f"{Fore.cyan}missings: {Style.reset}{dict(df.isna().sum())}")

#     #  * show first 3 rows
#     display(df[:3])

#     # ! *** PLOTS ***
#     if not use_plot:
#         return

#     # * set template
#     pio.templates.default = template

#     # * respect fig_offset to exclude unwanted plots from maintanance columns
#     cols = df.iloc[:, :fig_offset].columns
#     cols_num = df.select_dtypes(np.number).columns.tolist()
#     # cols_str = list(set(df.columns) - set(cols_num))

#     # * set constant column count, calc rows
#     fig_rows = math.ceil(len(cols) / fig_cols)

#     fig = make_subplots(
#         rows=fig_rows,
#         cols=fig_cols,
#         shared_xaxes=False,
#         shared_yaxes=False,
#         subplot_titles=cols,
#     )
#     # * layout settings
#     fig.layout.height = fig_rowheight * fig_rows
#     fig.layout.width = 400 * fig_cols

#     # * construct subplots
#     for i, col in enumerate(cols):
#         # * get unique values as sorted list
#         if sort_mode == "value":
#             span = df[col].value_counts().sort_values(ascending=False)
#         else:
#             span = df[col].value_counts().sort_index()

#         # * check if num col w/ too many values (disabled)
#         if col in cols_num and len(span) > 100 and False:
#             figsub = px.box(df, x=col, points="outliers")
#         else:
#             # * only respect 100 items
#             figsub = px.bar(
#                 x=span.iloc[:100].index,
#                 y=span.iloc[:100].values,
#             )
#         # * grid position
#         _row = math.floor((i) / fig_cols) + 1
#         _col = i % fig_cols + 1

#         # * add trace to fig, only data not layout, only 1 series
#         fig.add_trace(figsub["data"][0], row=_row, col=_col)

#     fig.show(renderer)

