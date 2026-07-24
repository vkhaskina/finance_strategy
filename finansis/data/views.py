from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.db.models import Min, Max, Sum, Count
from .models import Share

import csv
from datetime import datetime
import math
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from .serializers import ShareSerializer


# Create your views here.
@api_view(['POST'])
@csrf_exempt
@transaction.atomic
def read_input(request):
    csv_file = request.FILES.get('csv_file')

    if not csv_file:
        return Response({
            "status": "error",
            "message": "Файл не был загружен"
        },
            status=400)

    if not csv_file.name.endswith('.csv'):
        return Response({
            "status": "error",
            "message": "Пожалуйста, загрузите CSV-файл"
        },
            status=400)

    if Share.objects.filter(filename=csv_file.name).exists():
        return Response({
            "success": True,
            "message": f"Файл уже есть в БД",
            "filename": csv_file.name,
        },
            status=200
        )

    try:
        decoded_csv = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_csv, delimiter=';')

        shares_to_create = []
        shares_errors = []

        prev_close = {}
        with transaction.atomic():
            next(reader, None)
            for row_num, row  in enumerate(reader, start=1):

                print(row)

                cur_ticker = row[0].strip()
                cur_period = row[1].strip()
                str_date = row[2].strip()
                cur_open = float(row[4].strip().replace(',', '.'))
                cur_high = float(row[5].strip().replace(',', '.'))
                cur_low = float(row[6].strip().replace(',', '.'))
                cur_close = float(row[7].strip().replace(',', '.'))
                cur_vol = int(row[8].strip())

                #Сделкать тут расчеты доходностей и лобавить в БД!!!!
                if cur_ticker not in prev_close:
                    cur_profit_simple = None
                    cur_profit_ln =  None

                else:
                    prev = prev_close[cur_ticker]
                    if prev is not None and prev != 0:
                        profit_simple = (cur_close - prev) / prev
                        profit_ln = math.log(cur_close / prev)


                        cur_profit_simple = Decimal(str(profit_simple)).quantize(Decimal('0.0000'),
                                                                                 rounding=ROUND_HALF_UP)
                        cur_profit_ln = Decimal(str(profit_ln)).quantize(Decimal('0.0000'),
                                                                                 rounding=ROUND_HALF_UP)
                prev_close[cur_ticker] = cur_close


                try:
                    if len(str_date) == 8:
                        date_object = datetime.strptime(str_date, '%Y%m%d')
                    elif len(str_date) == 6:
                        date_object = datetime.strptime(str_date, '%y%m%d')
                    else:
                        raise ValueError(f"Неверная длина даты: {len(str_date)}")
                    cur_date = date_object.strftime('%Y-%m-%d')
                except ValueError:
                    shares_errors.append({
                        'row': row_num,
                        'error': f"Неверный формат даты"
                    })

                db_data = {
                    'filename': csv_file.name,
                    'ticker': cur_ticker,
                    'period': cur_period,
                    'date': cur_date,
                    'open': cur_open,
                    'high': cur_high,
                    'low': cur_low,
                    'close': cur_close,
                    'vol': cur_vol,
                    'profit_simple': cur_profit_simple,
                    'profit_ln': cur_profit_ln
                }

                serializer = ShareSerializer(data=db_data)
                if serializer.is_valid():
                    shares_to_create.append((Share(**serializer.validated_data)))
                else:
                    shares_errors.append({
                        'row': row_num,
                        'error': serializer.errors
                    })

            if shares_errors:
                return Response({
                    "status": "error",
                    "message": f"Некоторые строки не прошли валидацию {shares_errors}",
                },
                    status=400
                )

            Share.objects.bulk_create(shares_to_create)

            return Response({
                "success": True,
                "message": f"Загружено {len(shares_to_create)} записей",
                "filename": csv_file.name,
            },
                status=200
            )


    except UnicodeDecodeError:
        return Response({
            "status": "error",
            "message": "Ошибка в кодировке файла",
            },
            status=400
        )
    except IntegrityError as e:
        return Response({
            "status": "error",
            "message": f"Ошибка записи в БД {str(e)}",
        },
            status=400
        )
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Ошибка обработки csv: {str(e)}",
        },
            status=400
        )


@api_view(['POST', 'GET'])
@csrf_exempt
def graphs_data(request):
    filename = request.data.get('filename')
    graphs = request.data.get('graphs', [])

    if not filename:
        return Response({
            "status": "error",
            "message": "Не указано имя файла"
        },
            status=400)

    if not graphs:
        return Response({
            "status": "error",
            "message": "Не выбраны графики"
        },
            status=400)

    shares = Share.objects.filter(filename=filename).order_by('date')

    if not shares:
        return Response({
            "status": "error",
            "message": "Нет данных для файла"
        },
            status=400)

    response_data = {"status": "success", "data": {}}
    for graph_type in graphs:
        if graph_type == "Close":
            x = [share.date.strftime('%Y-%m-%d') for share in shares]
            y = [float(share.close) for share in shares]

            response_data["data"]["Close"] = {
                "x": x,
                "y": y,
                "title": "Цена закрытия",
                "xlabel": "Дата",
                "ylabel": "Цена"
            }
        elif graph_type == "Histogram":
            x = [share.date.strftime('%Y-%m-%d') for share in shares]
            y = [float(share.vol) for share in shares]

            response_data["data"]["Histogram"] = {
                "x": x,
                "y": y,
                "title": "Объем торгов",
                "xlabel": "Дата",
                "ylabel": "Объем"
            }
        elif graph_type == "Candles":
            x = [share.date.strftime('%Y-%m-%d') for share in shares]
            y = []
            for share in shares:
                y.append([
                    float(share.open),
                    float(share.close),
                    float(share.low),
                    float(share.high)
                ])

            y_min = shares.aggregate(Min('low'))['low__min']
            y_max = shares.aggregate(Max('high'))['high__max']

            response_data["data"]["Candles"] = {
                "x": x,
                "y": y,
                "title": "Японские свечи",
                "xlabel": "Дата",
                "ylabel": "Цена",
                # "ymin": y_min,
                # "ymax": y_max,
            }
            print(response_data)
    return Response(response_data)


@api_view(['GET', 'POST'])
@csrf_exempt
def analytics_data(request):
    if request.method == 'GET':
        filename = request.GET.get('filename')
    else:
        filename = request.data.get('filename')

    if not filename:
        return Response({
            "status": "error",
            "message": "Не указано имя файла"
        }, status=400)

    shares = Share.objects.filter(filename=filename).order_by('date')
    if not shares:
        return Response({
            "status": "error",
            "message": "Нет данных для файла"
        }, status=400)

    db_data = shares.order_by('date').values('date', 'close', 'profit_simple', 'profit_ln')
    df = pd.DataFrame.from_records(db_data)
    df['date'] = pd.to_datetime(df['date'])

    for col in ['close', 'profit_simple', 'profit_ln']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    mean_simple = df['profit_simple'].mean()
    mean_ln = df['profit_ln'].mean()
    std_simple = df['profit_simple'].std()
    std_ln = df['profit_ln'].std()

    if pd.isna(mean_simple):
        mean_simple = None
    if pd.isna(mean_ln):
        mean_ln = None
    if pd.isna(std_simple):
        std_simple = None
    if pd.isna(std_ln):
        std_ln = None

    first_share = shares.only('period').first()
    period = first_share.period if first_share else 'D'

    coeffs = {
        'H': 2268 ** 0.5,
        'D': 252 ** 0.5,
        'W': 52 ** 0.5,
        'M': 12 ** 0.5,
    }
    coeff = coeffs.get(period, 252 ** 0.5)

    mean_simple_annual = mean_simple * 252 if mean_simple is not None else None
    mean_ln_annual = mean_ln * 252 if mean_ln is not None else None
    std_simple_annual = std_simple * coeff if std_simple is not None else None
    std_ln_annual = std_ln * coeff if std_ln is not None else None

    volatility_simple = std_simple * coeff if std_simple is not None else None
    volatility_ln = std_ln * coeff if std_ln is not None else None

    sharpe_simple = (mean_simple_annual / std_simple_annual) if (
                mean_simple_annual is not None and std_simple_annual is not None and std_simple_annual != 0) else None
    sharpe_ln = (mean_ln_annual / std_ln_annual) if (
                mean_ln_annual is not None and std_ln_annual is not None and std_ln_annual != 0) else None

    df['cum_return'] = (1 + df['profit_simple'].fillna(0)).cumprod()
    df['peak'] = df['cum_return'].cummax()
    df['drawdown'] = (df['cum_return'] - df['peak']) / df['peak']
    max_drawdown = df['drawdown'].min()
    max_drawdown = abs(max_drawdown) if not pd.isna(max_drawdown) else None

    for i in [5, 10, 20, 30, 50]:
        df[f'SMA_{i}'] = df['close'].rolling(i).mean()

    df = df.where(pd.notnull(df), None)

    dates_str = df['date'].dt.strftime('%Y-%m-%d').tolist()

    response_data = {
        'dates': dates_str,
        'close': [None if pd.isna(x) else x for x in df['close'].tolist()],
        'profit_simple': [None if pd.isna(x) else x for x in df['profit_simple'].tolist()],
        'profit_ln': [None if pd.isna(x) else x for x in df['profit_ln'].tolist()],
        'sma_5': [None if pd.isna(x) else x for x in df['SMA_5'].tolist()],
        'sma_10': [None if pd.isna(x) else x for x in df['SMA_10'].tolist()],
        'sma_20': [None if pd.isna(x) else x for x in df['SMA_20'].tolist()],
        'sma_30': [None if pd.isna(x) else x for x in df['SMA_30'].tolist()],
        'sma_50': [None if pd.isna(x) else x for x in df['SMA_50'].tolist()],
        'statistics': {
            'mean_simple': mean_simple_annual,
            'mean_ln': mean_ln_annual,
            'std_simple': std_simple_annual,
            'std_ln': std_ln_annual,
            'volatility_simple': volatility_simple,
            'volatility_ln': volatility_ln,
            'sharpe_simple': sharpe_simple,
            'sharpe_ln': sharpe_ln,
            'max_drawdown': max_drawdown,
            'period': period,
        }
    }
    return Response(response_data)