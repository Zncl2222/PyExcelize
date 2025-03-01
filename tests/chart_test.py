from __future__ import annotations

import pytest

from pyfastexcel import Workbook
from pyfastexcel.chart import (
    Chart,
    ChartAxis,
    ChartCustomNumFmt,
    ChartLegend,
    ChartSeries,
    Font,
    GraphicOptions,
    Line,
    Marker,
    RichTextRun,
)
from pyfastexcel.enums import ChartDataLabelPosition, ChartLineType, ChartType, MarkerSymbol
from pyfastexcel.worksheet import WorkSheet


def get_wb() -> tuple[Workbook, WorkSheet]:
    wb = Workbook()
    ws = wb['Sheet1']

    for i in range(10):
        ws[i] = [i, i + 1, i + 2]

    return wb, ws


@pytest.mark.parametrize(
    'chart_type, expected_type',
    [
        ('Col', 21),
        ('COL', 21),
        ('cOL', 21),
        ('col', 21),
        (ChartType.Area, 0),
        (ChartType.Line, 41),
        (ChartType.Scatter, 48),
        (0, 0),
        (44, 44),
        (48, 48),
    ],
)
def test_chart_type(chart_type, expected_type):
    _, ws = get_wb()
    chart1 = Chart(
        chart_type=chart_type,
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            ),
        ],
    )
    ws.add_chart('C1', chart1)

    assert ws._chart_list[0]['chart'][0]['Type'] == expected_type


@pytest.mark.parametrize(
    'data_label_position, expected_type',
    [
        ('unset', 0),
        ('Unset', 0),
        ('uNSet', 0),
        ('UnSeT', 0),
        (ChartDataLabelPosition.BestFit, 1),
        (ChartDataLabelPosition.InsideEnd, 5),
        (ChartDataLabelPosition.OutsideEnd, 7),
        (7, 7),
        (8, 8),
        (9, 9),
    ],
)
def test_chart_series_data_label_position(data_label_position, expected_type):
    _, ws = get_wb()
    chart1 = Chart(
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
                data_label_position=data_label_position,
            )
        ],
    )
    ws.add_chart('C1', chart1)
    assert ws._chart_list[0]['chart'][0]['Series'][0]['DataLabelPosition'] == expected_type


@pytest.mark.parametrize(
    'symbol, expected_type',
    [
        ('cirCle', 'circle'),
        ('Circle', 'circle'),
        ('circle', 'circle'),
        ('cIRclE', 'circle'),
        (MarkerSymbol.Diamond, 'diamond'),
        (MarkerSymbol.Picture, 'picture'),
        (MarkerSymbol.Triangle, 'triangle'),
    ],
)
def test_chart_series_marker_symbol(symbol, expected_type):
    _, ws = get_wb()
    chart1 = Chart(
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
                marker=Marker(symbol=symbol),
            )
        ],
    )
    ws.add_chart('C1', chart1)
    assert ws._chart_list[0]['chart'][0]['Series'][0]['Marker']['Symbol'] == expected_type


@pytest.mark.parametrize(
    'ltype, expected_type',
    [
        ('solid', 1),
        ('Solid', 1),
        ('sOlId', 1),
        ('SoLId', 1),
        (ChartLineType.NONE, 2),
        (ChartLineType.Solid, 1),
        (ChartLineType.Automatic, 3),
        (1, 1),
        (0, 0),
        (2, 2),
    ],
)
def test_chart_series_line_ltype(ltype, expected_type):
    _, ws = get_wb()
    chart1 = Chart(
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
                line=Line(ltype=ltype),
            )
        ],
    )
    ws.add_chart('C1', chart1)
    assert ws._chart_list[0]['chart'][0]['Series'][0]['Line']['Type'] == expected_type


def test_marker_and_line_with_none_value():
    _, ws = get_wb()

    chart = Chart(
        chart_type='Line',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
                marker=Marker(symbol=None),
                line=Line(ltype=None),
            )
        ],
    )

    ws.add_chart('C1', chart)
    assert ws._chart_list[0]['chart'][0]['Series'][0]['Marker']['Symbol'] is None
    assert ws._chart_list[0]['chart'][0]['Series'][0]['Line']['Type'] is None


def test_add_chart2():
    wb, ws = get_wb()

    chart1 = Chart(
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            )
        ],
    )
    chart1 = Chart(
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            )
        ],
    )
    chart2 = Chart(
        chart_type='Line',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            )
        ],
        format=GraphicOptions(
            scale_x=1,
            scale_y=1,
            offset_x=15,
            offset_y=10,
            print_object=True,
            lock_aspect_ratio=False,
            locked=True,
        ),
        y_axis=ChartAxis(
            font=Font(
                bold=True,
                color='FF0000',
                size=19,
            ),
            num_fmt=ChartCustomNumFmt(num_fmt='0.00%'),
            title=[
                RichTextRun(
                    text='Y軸',
                )
            ],
        ),
        x_axis=ChartAxis(
            font=Font(
                color='00FF00',
                size=26,
            ),
            title=[
                RichTextRun(
                    text='X軸',
                )
            ],
        ),
        title=[RichTextRun(text='群組柱形圖 - 折線圖', font=Font(bold=True, color='#FF0000'))],
        legend=ChartLegend(
            position='left',
            show_legend_key=True,
        ),
    )
    ws.add_chart(
        'G1',
        [chart1, chart2],
    )
    ws.add_chart(
        'XD1',
        chart1,
    )

    ws.add_chart(
        'N1',
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            )
        ],
        legend=ChartLegend(position='left'),
    )

    wb.add_chart(
        'Sheet1',
        'XG1',
        chart1,
    )

    wb.add_chart(
        'Sheet1',
        'XG15',
        [chart1, chart2],
    )

    wb.add_chart(
        'Sheet1',
        'R1',
        chart_type='Col',
        series=[
            ChartSeries(
                name='Sheet1!$A$2',
                categories='Sheet1!$B$2:$C$2',
                values='Sheet1!$B$3:$C$3',
            )
        ],
        legend=ChartLegend(position='left'),
    )

    wb.read_lib_and_create_excel()


def test_add_chart_failed():
    wb, _ = get_wb()

    with pytest.raises(ValueError):
        wb.add_chart(
            'Sheet1',
            'XG1',
            chart_model=None,
        )
