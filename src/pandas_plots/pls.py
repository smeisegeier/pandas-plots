import warnings
warnings.filterwarnings('ignore')

import os
from typing import Literal
from matplotlib import pyplot as plt
from plotly import express as px
import pandas as pd
import seaborn as sb

def _set_caption(caption: str) -> str:
    return f"#️⃣{'-'.join(caption.split())}, " if caption else ""


def plot_quadrants(
    df: pd.DataFrame, 
    title: str= None,
    caption: str=None,
    ) -> None:
    """
    Plot a heatmap for the given dataframe, with options for title and caption.

    Args:
        df (pd.DataFrame): The input dataframe with 2 or 3 columns.
            df must have 3 columns, first 2 must be present
                index axis
                columns axis
                values (can be derived as cnt=1)
            df columns must contain 2 values
        title (str, optional): The title for the heatmap to override the default. 
        caption (str, optional): The caption for the heatmap. Defaults to None.

    Returns:
        q1, q2, q3, q4, n: The values for each quadrant and the total count.
    """
    if len(df.columns) < 2 or len(df.columns) > 3:
        print('❌ df must have 2 or 3 columns')
        return

    if len(df.iloc[:,0].unique()) != 2 or len(df.iloc[:,0].unique()) != 2:
        print('❌ both columns must have 2 values')
        return
    
    if len(df.columns) == 2:
        df['cnt'] = 1
    
    heat = (df.groupby(
        by=[df.columns[0], df.columns[1]],
        as_index=True,          # * use index to keep track of all columns
        )[df.columns[2]]
        .sum().reset_index()    # * then reset index to get a dataframe with all columns
        )
    # * create pivot table in wide format for heatmap
    heat_wide=heat.pivot(
        index=df.columns[0],
        columns=df.columns[1], 
        values=df.columns[2],
        )

    # * derive label for heatmap
    n = heat_wide.sum().sum()
    heat_label = heat_wide.map(lambda x: f'{x:_}\n({x/n*100:.1f}%)')
    
    # * seaborn. use less fancy stuff :)
    caption= f'#{caption.lower()}, ' if caption else 'heatmap, '

    # * plot
    theme='dark_background' if os.getenv('THEME')=='dark' else 'ggplot'
    
    plt.style.use(theme)
    _=sb.heatmap(
        # data=_heat_wide,
        data=heat_wide.map(lambda x: x/n),
        annot=heat_label,
        fmt='',
        cmap='BuPu',
        vmin=0,     # * to have relative values in colorbar
        vmax=1,
        
        ).set_title(f'{caption}n = {n:_.0f}' if not title else title)
    
    # * dont output na values
    heat_wide_out=heat_wide.fillna(0)
    q1=heat_wide_out.iloc[1,1]
    q2=heat_wide_out.iloc[1,0]
    q3=heat_wide_out.iloc[0,0]
    q4=heat_wide_out.iloc[0,1]

    return q1, q2, q3, q4, n
    # * plotly express is not used for the heatmap, although it does not need the derived wide format.
    # * but theres no option to alter inner values in the heatmap

def plot_stacked_bars(
    df: pd.DataFrame,
    top_n_index: int = 0,
    top_n_color: int = 0,
    dropna: bool = False,
    swap: bool = False,
    normalize: bool = False,
    relative: bool = False,
    orientation: Literal["h", "v"] = "v",
    height: int=500,
    width: int=2000,
    title: str = None,
    renderer: Literal["png", "svg",None] = "png",
    caption: str=None,
    sort_values: bool=False,
    show_total: bool=False,
) -> None:
    """
    Generates a stacked bar plot using the provided DataFrame.
    df *must* comprise the columns (order matters):
    - index axis
    - color axis (legend)
    - values (optional, if absent a simple count is applied)

    Parameters:
    - df: pd.DataFrame - The DataFrame containing the data to plot.
    - top_n_index: int = 0 - The number of top indexes to include in the plot.
    - top_n_index: int = 0 - The number of top colors to include in the plot. WARNING: this forces distribution to 100% on a subset
    - dropna: bool = False - Whether to include NULL values in the plot.
    - swap: bool = False - Whether to swap the x-axis and y-axis.
    - normalize: bool = False - Whether to normalize the values.
    - relative: bool = False - Whether to show relative values as bars instead of absolute.
    - orientation: Literal["h", "v"] = "v" - The orientation of the plot.
    - height: int = 500 - The height of the plot.
    - width: An optional integer indicating the width of the chart. Default is 2000.
    - title: str = None - The title of the plot.
    - renderer: Literal["png", "svg",None] = "png" - The renderer for the plot.
    - caption: An optional string indicating the caption for the chart.
    - sort_values: bool = False - Sort axis by index (default) or values
    - show_total: bool = False - Whether to show the total value

    Returns:
    None
    """
    BAR_LENGTH_MULTIPLIER=1.05

    # * 2 axis means at least 2 columns
    if len(df.columns) < 2 or len(df.columns) > 3:
        print("❌ df must have exactly 2 or 3 columns")
        return

    # * check if first 2 columns are str
    if list(set((df.iloc[:, [0,1]].dtypes)))[0].kind != 'O':
        print("❌ first 2 columns must be str")
        return

    # * add count column[2] as a service if none is present
    if len(df.columns) == 2:
        df["cnt"] = 1

    # * create seperate section for na values if selected
    if not dropna:
        df = df.fillna('<NA>')
    else:
        df.dropna(inplace=True)

    # * strip whitespaces
    df.iloc[:,0] = df.iloc[:,0].str.strip()
    df.iloc[:,1] = df.iloc[:,1].str.strip()

    # * set index + color col
    col_index = df.columns[0] if not swap else df.columns[1]
    col_color = df.columns[1] if not swap else df.columns[0]
    
    # * add total as aggregation of df
    if show_total:
        df_total=df.copy()
        df_total[col_index]=' TOTAL'    # add space to make this item first
        df=pd.concat([df,df_total])

    # * ensure df is grouped to prevent false aggregations
    df = (df.groupby([
            df.columns[0], 
            df.columns[1],
        ])[df.columns[2]]
        .sum()
        .reset_index()
    )

    # * calculate n
    divider=2 if show_total else 1
    n = int(df[df.columns[2]].sum() / divider)

    # * after grouping add cols for pct and formatting
    df['cnt_pct'] = df[df.columns[2]] / n                               # * col[3]
    df['cnt_str']= df[df.columns[2]].apply(lambda x: f"{x:_}")      # * col[4]
    df['cnt_pct_str'] = df['cnt_pct'].apply(lambda x: f"{x:.2%}")   # * col[5]

    # * now set calculated col
    col_value = df.columns[2] if not normalize else df.columns[3]
    col_value_str = df.columns[4] if not normalize else df.columns[5]

    if top_n_index > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n = (
            df.groupby(col_index)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_index]
        )
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]

    if top_n_color > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n_col = (
            df.groupby(col_color)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_color]
        )
        # * only process top n colors. this does not change pct values
        df = df[df[col_color].isin(ser_top_n_col.index)]

    # * get longest bar
    bar_max = (
        df.groupby(col_index)[col_value].sum().sort_values(ascending=False).iloc[0] * BAR_LENGTH_MULTIPLIER
    )

    # * are TOP n selected? include in default title
    _title_str_top_index = f"TOP{top_n_index} " if top_n_index > 0 else ""
    _title_str_top_color = f"TOP{top_n_color} " if top_n_color > 0 else ""
    
    # * title str na
    _title_str_null = f", NULL excluded" if dropna else ""

    # * title str n
    _title_str_n = f", n={n:_}"
    
    caption=_set_caption(caption)

    # * plot
    _fig = px.bar(
        df,
        x=col_index if orientation == "v" else col_value,
        y=col_value if orientation == "v" else col_index,
        color=col_color,
        text=col_value_str,
        # barmode="stack",
        orientation=orientation,
        title=title or f"{caption}{_title_str_top_index}[{col_index}] by {_title_str_top_color}[{col_color}]{_title_str_null}{_title_str_n}",
        # * retrieve theme from env (intro.set_theme) or default
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        width=width,
        height=height,
    )
    
    # * ignore if bar mode is on 
    if not relative:
        if orientation == "v":
            _fig.update_yaxes(range=[0, bar_max])
        else:
            _fig.update_xaxes(range=[0, bar_max])
    else:
        _fig.update_layout(barnorm='percent')

    # * set title properties
    _fig.update_layout(
        title={
            # 'x': 0.1,
            'y': 0.95,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'size': 24, }
        },
    )

    # * show grids, set to smaller distance on pct scale
    _fig.update_xaxes(
        showgrid=True, 
        gridwidth=1,
        dtick=.05 if orientation == "h" and normalize else 5 if orientation == "h" and relative else None,
        )
    _fig.update_yaxes(
        showgrid=True, 
        gridwidth=1,
        dtick=.05 if orientation == "v" and normalize else 5 if orientation == "v" and relative else None,
        )

    # * sorting is in a weird spot, do a 1:1 matrix
    if orientation == "v" and sort_values:
        _fig.update_layout(xaxis={'categoryorder':"total descending"})
    elif orientation == "v" and not sort_values:
        _fig.update_layout(xaxis={'categoryorder':"category ascending"})
    elif orientation == "h" and sort_values:
        _fig.update_layout(yaxis={'categoryorder':"total ascending"})
    elif orientation == "h" and not sort_values:
        _fig.update_layout(yaxis={'categoryorder':"category descending"})

    _fig.show(renderer)
    return


def plot_bars(
    ser: pd.Series | pd.DataFrame,
    caption: str=None,
    top_n_index: int = 0,
    top_n_minvalue: int = 0,
    dropna: bool = False,
    orientation: Literal["h", "v"] = "v",
    sort_values: bool = False,
    normalize: bool = False,
    height: int=500,
    width: int=1600,
    title: str = None,
    renderer: Literal["png", "svg",None] = "png",
) -> None:
    """
    A function to plot a bar chart based on a pandas Series.
    Accepts series or dataframe w/ 2 columns (index, value)

    Parameters:
    - ser: The input pandas Series.
    - caption: An optional string indicating the caption for the chart.
    - top_n_index: An optional integer indicating the number of top indexes to include in the chart. Default is 0, which includes all indexes.
    - top_n_minvalue: An optional integer indicating the minimum value to be included in the chart. Default is 0, which includes all values.
    - dropna: A boolean indicating whether to drop NaN values from the chart. Default is False.
    - orientation: A string indicating the orientation of the chart. It can be either "h" for horizontal or "v" for vertical. Default is "v".
    - sort_values: A boolean indicating whether to sort the values in the chart. Default is False.
    - nomalize: A boolean indicating whether to show pct values in the chart. Default is False.
    - height: An optional integer indicating the height of the chart. Default is 500.
    - width: An optional integer indicating the width of the chart. Default is 2000.
    - title: An optional string indicating the title of the chart. If not provided, the title will be the name of the index column.
    - renderer: A string indicating the renderer to use for displaying the chart. It can be "png", "svg", or None. Default is "png".

    Returns:
    - None
    """

    # * if a df is given, convert to series
    if isinstance(ser, pd.DataFrame):
        if len(ser.columns) != 2:
            print("❌ df must have exactly 2 columns")
            return
        else:
            # * save index name
            _idx_name=ser.columns[0]
            ser = pd.Series(
                index=ser.iloc[:,0].values, 
                data=ser.iloc[:,1].values,
                name=ser.columns[1],)
            # * restore index name, otherwise this gets lost during groupby
            ser.index.name= _idx_name

    # * ensure df is grouped to prevent false aggregations
    df=ser.groupby(ser.index, dropna=False).sum().reset_index()

    # * nulls are hidden by default in plotly etc, so give them a proper category
    if dropna:
        df = df.dropna()
    else:
        df = df.fillna('<NA>')

    # * get n
    n = df[df.columns[1]].sum()

    # * after grouping add cols for pct and formatting
    df['pct'] = df[df.columns[1]] / n     # * col[2]
    df['cnt_str']= df[df.columns[1]].apply(lambda x: f"{x:_}")      # * col[3]
    divider='<br>' if orientation=='v' else ' '
    df['cnt_pct_str'] = df.apply(lambda row: f"{row['cnt_str']}{divider}({row['pct']:.1%})", axis=1)   # * col[4]
    # df['cnt_pct_str'] = df['pct'].apply(lambda x: f"{x:.2%}")   # * col[4]

    # * set col vars 0-5 according to config
    col_index = df.columns[0]
    col_value = df.columns[2]
    col_value_str = df.columns[4] if normalize else df.columns[3]

    # * if top n selected
    if top_n_index > 0:
        # * get top n -> series
        # * on pivot tables (all cells are values) you can also use sum for each column[df.sum(axis=1) > n]
        ser_top_n = (
            df.groupby(col_index, dropna=False)[col_value]
            .sum()
            .sort_values(ascending=False)[:top_n_index]
        )
        # * only process top n indexes. this does not change pct values
        df = df[df[col_index].isin(ser_top_n.index)]
        
    # * if top n min value: filter out below threshold
    if top_n_minvalue > 0:
        df=df[df.iloc[:,1] >= top_n_minvalue]

    # * get longest bar
    bar_length_multiplier = 1.1 if normalize else 1.05
    bar_max = (
        df.groupby(col_index, dropna=False)[col_value].sum().sort_values(ascending=False).iloc[0] * bar_length_multiplier
    )

    # * are TOP n selected? include in default title
    _title_str_top = f"TOP {top_n_index} " if top_n_index > 0 else ""

    # * are TOP n selected? include in default title
    _title_str_minval = f"ALL >{top_n_minvalue}, " if top_n_minvalue > 0 else ""

    # * title str n
    _title_str_n = f", n={n:_}"

    # * title str na
    _title_str_null = f", NULL excluded" if dropna else ""
    
    # * layot caption if provided
    caption = _set_caption(caption)

    # * plot
    _fig = px.bar(
        df.sort_values(
            col_value if sort_values else col_index,
            ascending=False if sort_values else True,
            ),
        x=col_index if orientation == "v" else col_value,
        y=col_value if orientation == "v" else col_index,
        text=col_value_str,
        orientation=orientation,
        title=title or f"{caption}{_title_str_minval}{_title_str_top}[{col_index}]{_title_str_null}{_title_str_n}",
        # * retrieve theme from env (intro.set_theme) or default
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        width=width,
        height=height,
    )
    
    if orientation == "v":
        _fig.update_yaxes(range=[0, bar_max * 1.05])  # let extra space if vertical
    else:
        _fig.update_xaxes(range=[0, bar_max])

    # * show grids
    _fig.update_xaxes(
        showgrid=True, 
        gridwidth=1,
        dtick=.05 if orientation == "h" else None,
        )
    _fig.update_yaxes(
        showgrid=True, 
        gridwidth=1,
        dtick=.05 if orientation == "v" else None,
        )

    # * set title properties
    _fig.update_layout(
        title={
            # 'x': 0.1,
            'y': 0.95,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'size': 24, }
        },
    )
    # * sorting
    if orientation == "v":
        if sort_values:
            _fig.update_layout(xaxis={'categoryorder':"total descending"})
        else:
            _fig.update_layout(xaxis={'categoryorder':"category ascending"})
    else:
        if sort_values:
            _fig.update_layout(yaxis={'categoryorder':"total ascending"})
        else:
            _fig.update_layout(yaxis={'categoryorder':"category descending"})
    
    # * looks better on single bars
    _fig.update_traces( textposition='outside')
    _fig.show(renderer)
    return


def plot_box(
    ser: pd.Series, 
    points: Literal['all', 'outliers', 'suspectedoutlieres', None] = None,
    precision: int=2,
    height: int=200,
    width: int=1200,
    annotations: bool=True,
    caption: str=None,
    title: str=None,
    violin: bool=False,
    ) -> None:
    """
    Plots a box plot for the given pandas Series.

    Args:
        ser: The pandas Series to plot.
        points: The type of points to plot on the box plot ('all', 'outliers', 'suspectedoutliers', None).
        precision: The precision of the annotations.
        height: The height of the plot.
        width: The width of the plot.
        annotations: Whether to add annotations to the plot.
        violin: Use violin plot or not

    Returns:
        None
    """
    
    if not pd.api.types.is_numeric_dtype(ser):
        print(f"❌ series {ser.name} is not numeric")
        return
    
    median=ser.median()
    mean=ser.mean()
    q25=ser.quantile(0.25)
    q75=ser.quantile(0.75)
    min=ser.min()
    max=ser.max()
    fence0_=q25-1.5*(q75-q25)
    fence0= fence0_ if fence0_ > min else min
    fence1_=q75+1.5*(q75-q25)
    fence1= fence1_ if fence1_ < max else max
    lvl1=height*0.05
    lvl2=height*0.15
    lvl3=height*0.25
    
    caption=_set_caption(caption)

    dict={
        'data_frame':ser, 
        'orientation':'h',
        'template':'plotly_dark' if os.getenv('THEME') == 'dark' else 'plotly',
        'height':height,
        'width':width,
        'points':points,
        # 'box':True,
        'title':f"{caption}[{ser.name}], n = {len(ser):_}" if not title else title,
        }

    fig=px.violin(**{**dict,'box':True}) if violin else px.box(**dict)

    # fig=px.violin(
    #     ser, 
    #     template=os.getenv('THEME_PLOTLY'),
    #     orientation='h',
    #     height=height,
    #     width=width,
    #     points=points,
    #     box=True,
    #     title=f"{caption}[{ser.name}], n = {len(ser):_}" if not title else title,
    #     )
    if annotations:
        fig.add_annotation(x=min, text=f"min: {round(min,precision)}", showarrow=True, yshift=lvl1, y=-0)
        fig.add_annotation(x=fence0, text=f"lower: {round(fence0,precision)}", showarrow=True, yshift=lvl3, y=-0)
        fig.add_annotation(x=q25, text=f"q25: {round(q25,precision)}", showarrow=True, yshift=lvl2, y=-0)
        fig.add_annotation(x=median, text=f"median: {round(median,precision)}", showarrow=True, yshift=lvl1, y=-0)
        fig.add_annotation(x=mean, text=f"mean: {round(mean,precision)}", showarrow=True, yshift=lvl3, y=-0)
        fig.add_annotation(x=q75, text=f"q75: {round(q75,precision)}", showarrow=True, yshift=lvl2, y=-0)
        fig.add_annotation(x=fence1, text=f"upper: {round(fence1,precision)}", showarrow=True, yshift=lvl1, y=-0)
        fig.add_annotation(x=max, text=f"max: {round(max,precision)}", showarrow=True, yshift=lvl3, y=-0)
    fig.show('png')
    return

def plot_boxes(
    df: pd.DataFrame,
    caption: str=None,
    points: Literal["all", "outliers", "suspectedoutliers", None] = None,
    precision: int = 2,
    height: int = 600,
    width: int = 800,
    annotations: bool = True,
    title: str=None
) -> None:
    """
    Plot boxes for each unique item in the DataFrame and add annotations for statistics.
    
    Args:
        df (pd.DataFrame): The input DataFrame with two columns, where the first column is string type and the second column is numeric.
        caption (str): The caption for the plot.
        points (Literal["all", "outliers", "suspectedoutliers", None]): The points to be plotted.
        precision (int): The precision for rounding the statistics.
        height (int): The height of the plot.
        width (int): The width of the plot.
        annotations (bool): Whether to add annotations to the plot.
    
    Returns:
        None
    """

    if (
        len(df.columns) != 2
        or not pd.api.types.is_string_dtype(df.iloc[:, 0])
        or not pd.api.types.is_numeric_dtype(df.iloc[:, 1])
    ):
        print(f"❌ df must have 2 columns: [0] str, [1] num")
        return
    # * layout gaps
    xlvl1 = -50
    xlvl2 = 0
    xlvl3 = 50

    # * not working
    # yspan_seg = (df.iloc[:, 1].max() - df.iloc[:, 1].max()) * .05
    # ylvl1 = -yspan_seg
    # ylvl2 = 0
    # ylvl3 = yspan_seg
    
    # * unique items
    items = df.iloc[:,0].unique()
    
    caption=_set_caption(caption)

    # * main plot
    fig = px.box(
        df,
        x=df.iloc[:, 0],
        y=df.iloc[:, 1],
        template="plotly_dark" if os.getenv("THEME") == "dark" else "plotly",
        orientation="v",
        height=height,
        width=width,
        points=points,
        title=f"{caption}[{df.columns[0]}] on [{df.columns[1]}], n = {len(df):_.0f}" if not title else title,
    )

    # * yshift is trivial
    YS=0

    # * loop annotations
    if annotations:
        for i,item in enumerate(items):
            max = round(df[df.iloc[:,0] == item].iloc[:,1].max(), precision)
            min = round(df[df.iloc[:,0] == item].iloc[:,1].min(), precision)
            mean = round(df[df.iloc[:,0] == item].iloc[:,1].mean(), precision)
            median = round(df[df.iloc[:,0] == item].iloc[:,1].median(), precision)
            q25 = round(df[df.iloc[:,0] == item].iloc[:,1].quantile(.25), precision)
            q75 = round(df[df.iloc[:,0] == item].iloc[:,1].quantile(.75), precision)
            fence0_ = round(q25 - 1.5 * (q75 - q25), precision)
            fence0 = fence0_ if fence0_ > min else min
            fence1_ = round(q75 + 1.5 * (q75 - q25), precision)
            fence1 = fence1_ if fence1_ < max else max
            fig.add_annotation(x=i, y=min, text=f"min: {min}", yshift=YS, showarrow=True,xshift=xlvl1)
            fig.add_annotation(x=i, y=fence0, text=f"lower: {fence0}", yshift=YS, showarrow=True,xshift=xlvl3)
            fig.add_annotation(x=i, y=q25, text=f"q25: {q25}", yshift=YS, showarrow=True,xshift=xlvl2)
            fig.add_annotation(x=i, y=mean, text=f"mean: {mean}", yshift=YS, showarrow=True,xshift=xlvl1)
            fig.add_annotation(x=i, y=median, text=f"median: {median}", yshift=YS, showarrow=True,xshift=xlvl3)
            fig.add_annotation(x=i, y=q75, text=f"q75: {q75}", yshift=YS, showarrow=True,xshift=xlvl2)
            fig.add_annotation(x=i, y=fence1, text=f"upper: {fence1}", yshift=YS, showarrow=True,xshift=xlvl3)
            fig.add_annotation(x=i, y=max, text=f"max: {max}", yshift=YS, showarrow=True, xshift=xlvl1)

    fig.update_xaxes(title_text=df.columns[0])
    fig.update_yaxes(title_text=df.columns[1])
    fig.show("png")
    return