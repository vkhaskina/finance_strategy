# from django.shortcuts import render
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from django.db import IntegrityError, transaction
# from data.models import Share
#
# import pandas as pd
# import numpy as np
#
# @api_view(['POST'])
# @csrf_exempt
# def strategy_data(request):
#     filename = request.data.get('filename')
#     ema_fast = int(request.data.get('ema_fast', 12))
#     ema_slow = int(request.data.get('ema_slow', 26))
#     rsi_period = int(request.data.get('rsi_period', 14))
#     macd_signal = int(request.data.get('macd_signal', 9))
#
#     if not filename:
#         return Response({
#             "status": "error",
#             "message": "Не указано имя файла"
#         },
#             status=400)
#
#     shares = Share.objects.filter(filename=filename).order_by('date')
#
#     if not shares:
#         return Response({
#             "status": "error",
#             "message": "Нет данных для файла"
#         },
#             status=400)
#
#     db_data = shares.order_by('date').values('date', 'close')
#     df = pd.DataFrame.from_records(db_data)
#     df['date'] = pd.to_datetime(df['date'])
#     df['close'] = df['close'].astype(float)
#
#     df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
#     df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
#
#     delta = df['close'].diff()
#     gain = delta.clip(lower = 0)
#     loss = -delta.clip(upper = 0)
#
#     avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     rs = avg_gain / avg_loss
#     df['rsi'] = 100 - (100 / (1 + rs))
#     df.loc[:rsi_period-1, 'rsi'] = np.nan
#
#     df['macd_line'] = df['ema_fast'] - df['ema_slow']
#     df['macd_signal'] = df['macd_line'].ewm(span=macd_signal, adjust=False).mean()
#     df['macd_histogram'] = df['macd_line'] - df['macd_signal']
#
#     df = df.replace([np.nan, np.inf, -np.inf], None)
#
#     response_data = {
#         'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
#         'close': df['close'].tolist(),
#         'ema_fast': df['ema_fast'].tolist(),
#         'ema_slow': df['ema_slow'].tolist(),
#         'rsi': df['rsi'].tolist(),
#         'macd_line': df['macd_line'].tolist(),
#         'macd_signal': df['macd_signal'].tolist(),
#         'macd_histogram': df['macd_histogram'].tolist()
#     }
#
#     return Response(response_data)
#
# @api_view(['GET', 'POST'])
# @csrf_exempt
# def strategy_test(request):
#     filename = request.data.get('filename')
#     ema_fast = int(request.data.get('ema_fast', 12))
#     ema_slow = int(request.data.get('ema_slow', 26))
#     rsi_period = int(request.data.get('rsi_period', 14))
#     macd_signal = int(request.data.get('macd_signal', 9))
#     rsi_oversold = int(request.data.get('rsi_oversold', 50))
#     rsi_overbought = int(request.data.get('rsi_overbought', 50))
#     initial_capital = float(request.data.get('initial_capital', 10000))
#
#     if not filename:
#         return Response({
#             "status": "error",
#             "message": "Не указано имя файла"
#         },
#             status=400)
#
#
#     shares = Share.objects.filter(filename=filename).order_by('date')
#
#     if not shares:
#         return Response({
#             "status": "error",
#             "message": "Нет данных для файла"
#         },
#             status=400)
#
#     db_data = shares.order_by('date').values('date', 'close')
#     df = pd.DataFrame.from_records(db_data)
#     df['date'] = pd.to_datetime(df['date'])
#     df['close'] = df['close'].astype(float)
#
#     df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
#     df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
#
#     delta = df['close'].diff()
#     gain = delta.clip(lower = 0)
#     loss = -delta.clip(upper = 0)
#
#     avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     rs = avg_gain / avg_loss
#     df['rsi'] = 100 - (100 / (1 + rs))
#     df.loc[:rsi_period-1, 'rsi'] = np.nan
#
#     df['macd_line'] = df['ema_fast'] - df['ema_slow']
#     df['macd_signal'] = df['macd_line'].ewm(span=macd_signal, adjust=False).mean()
#
#     #df = df.where(pd.notnull(df), None)
#
#     start_index = max(ema_slow, rsi_period, macd_signal)
#     in_position = False
#     position_type = None
#     entry_price = 0.0
#     trades = []
#     signals = []
#
#     print(f"Длина DataFrame: {len(df)}")
#     print(f"start_index: {start_index}")
#     print(df[['close', 'ema_fast', 'ema_slow', 'rsi', 'macd_line', 'macd_signal']].iloc[start_index:start_index + 5])
#
#     for i in range(start_index, len(df)):
#         curr = df.iloc[i]
#         prev = df.iloc[i-1]
#
#         if (pd.isna(curr.ema_fast) or pd.isna(curr.ema_slow) or pd.isna(curr.rsi) or
#                 pd.isna(curr.macd_line) or pd.isna(curr.macd_signal) or
#                 pd.isna(prev.macd_line) or pd.isna(prev.macd_signal)):
#             continue
#
#         long_condition = (
#             curr.ema_fast > curr.ema_slow) and (
#             curr.rsi < rsi_oversold) and (
#             prev.macd_line <= prev.macd_signal and
#             curr.macd_line > curr.macd_signal)
#
#         short_condition = (
#             curr.ema_fast < curr.ema_slow) and (
#             curr.rsi > rsi_overbought) and (
#             prev.macd_line >= prev.macd_signal and
#             curr.macd_line < curr.macd_signal)
#
#         # long_condition = curr.ema_fast > curr.ema_slow
#         # short_condition = curr.ema_fast < curr.ema_slow
#
#         if not in_position:
#             if long_condition:
#                 in_position = True
#                 position_type = 'long'
#                 entry_price = curr.close
#                 entry_date = curr.date
#
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'buy',
#                     'price': float(curr.close)
#                 })
#             elif short_condition:
#                 in_position = True
#                 position_type = 'short'
#                 entry_price = curr.close
#                 entry_date = curr.date
#
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'buy',
#                     'price': float(curr.close)
#                 })
#         else:
#             if position_type == 'long' and short_condition:
#                 exit_price = curr.close
#                 ret = (exit_price - entry_price) / entry_price
#
#                 trades.append({
#                     "entry_date": entry_date.strftime('%Y-%m-%d'),
#                     "entry_price": float(entry_price),
#                     "exit_date": curr.date.strftime('%Y-%m-%d'),
#                     "exit_price": float(exit_price),
#                     "type": "long",
#                     "return_pct": float(ret)
#                 })
#
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'sell',
#                     'price': float(exit_price)
#                 })
#
#                 position_type = 'short'
#                 entry_price = curr.close
#                 entry_date = curr.date
#
#             elif position_type == 'short' and long_condition:
#                 exit_price = curr.close
#                 ret = (entry_price - exit_price) / entry_price
#
#                 trades.append({
#                     "entry_date": entry_date.strftime('%Y-%m-%d'),
#                     "entry_price": float(entry_price),
#                     "exit_date": curr.date.strftime('%Y-%m-%d'),
#                     "exit_price": float(exit_price),
#                     "type": "short",
#                     "return_pct": float(ret)
#                 })
#
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'sell',
#                     'price': float(exit_price)
#                 })
#
#                 position_type = 'long'
#                 entry_price = curr.close
#                 entry_date = curr.date
#
#     if in_position:
#         exit_price = df.iloc[-1]['close']
#         exit_date = df.iloc[-1]['date']
#         if position_type == 'long':
#             ret = (exit_price - entry_price) / entry_price
#         else:
#             ret = (entry_price - exit_price) / entry_price
#         trades.append({
#             "entry_date": entry_date.strftime('%Y-%m-%d'),
#             "entry_price": float(entry_price),
#             "exit_date": exit_date.strftime('%Y-%m-%d'),
#             "exit_price": float(exit_price),
#             "type": "short",
#             "return_pct": float(ret)
#         })
#
#         signals.append({
#             'date': exit_date.strftime('%Y-%m-%d'),
#             'type': 'sell',
#             'price': float(exit_price)
#         })
#
#     total_trades = len(trades)
#     winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
#     win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
#
#     portfolio_return = 1.0
#     for t in trades:
#         portfolio_return *= (1 + t['return_pct'])
#     total_return = portfolio_return - 1
#
#     first_close = df.iloc[0]['close']
#     last_close = df.iloc[-1]['close']
#     buy_hold_return = (last_close - first_close) / first_close
#
#     capital = initial_capital
#     equity = [capital]
#     for t in trades:
#         capital *= (1 + t['return_pct'])
#         equity.append(capital)
#
#     peak = equity[0]
#     max_drawdown = 0
#     for val in equity:
#         if val > peak:
#             peak = val
#         dd = (val - peak) / peak
#         if dd < max_drawdown:
#             max_drawdown = dd
#
#     response_data = {
#         "status": "success",
#         "trades": trades,
#         "signals": signals,
#         "statistics": {
#             "total_trades": total_trades,
#             "winning_trades": winning_trades,
#             "win_rate": round(win_rate, 2),
#             "total_return": round(total_return, 4),
#             "buy_hold_return": round(buy_hold_return, 4),
#             "max_drawdown": round(max_drawdown, 4)
#         }
#     }
#     return Response(response_data)
#
#
#
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from data.models import Share

import pandas as pd
import numpy as np


def get_indicator_dataframe(filename, ema_fast=12, ema_slow=26, rsi_period=14, macd_signal=9):
    shares = Share.objects.filter(filename=filename).order_by('date')
    if not shares:
        return None, "Нет данных для файла", 400

    db_data = shares.values('date', 'close')
    df = pd.DataFrame.from_records(db_data)
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = df['close'].astype(float)

    df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()

    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period, adjust=False).mean()
    avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[:rsi_period - 1, 'rsi'] = np.nan

    df['macd_line'] = df['ema_fast'] - df['ema_slow']
    df['macd_signal'] = df['macd_line'].ewm(span=macd_signal, adjust=False).mean()
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']

    df = df.replace([np.nan, np.inf, -np.inf], None)

    return df, None, None


@api_view(['POST'])
@csrf_exempt
def strategy_data(request):
    filename = request.data.get('filename')
    ema_fast = int(request.data.get('ema_fast', 12))
    ema_slow = int(request.data.get('ema_slow', 26))
    rsi_period = int(request.data.get('rsi_period', 14))
    macd_signal = int(request.data.get('macd_signal', 9))

    if not filename:
        return Response({"status": "error", "message": "Не указано имя файла"}, status=400)

    df, err_msg, err_status = get_indicator_dataframe(filename, ema_fast, ema_slow, rsi_period, macd_signal)
    if err_msg:
        return Response({"status": "error", "message": err_msg}, status=err_status)

    response_data = {
        'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'close': df['close'].tolist(),
        'ema_fast': df['ema_fast'].tolist(),
        'ema_slow': df['ema_slow'].tolist(),
        'rsi': df['rsi'].tolist(),
        'macd_line': df['macd_line'].tolist(),
        'macd_signal': df['macd_signal'].tolist(),
        'macd_histogram': df['macd_histogram'].tolist()
    }
    return Response(response_data)

#
# @api_view(['POST'])
# @csrf_exempt
# def strategy_test(request):
#     # Параметры стратегии
#     filename = request.data.get('filename')
#     ema_period = int(request.data.get('ema_period', 20))          # n
#     rsi_period = int(request.data.get('rsi_period', 14))          # m
#     rsi_oversold = int(request.data.get('rsi_oversold', 30))      # α
#     rsi_overbought = int(request.data.get('rsi_overbought', 50))  # β
#     stop_loss_pct = float(request.data.get('stop_loss_pct', 0.05)) # s
#     initial_capital = float(request.data.get('initial_capital', 10000))
#
#     if not filename:
#         return Response({"status": "error", "message": "Не указано имя файла"}, status=400)
#
#     # Загрузка данных
#     shares = Share.objects.filter(filename=filename).order_by('date')
#     if not shares:
#         return Response({"status": "error", "message": "Нет данных для файла"}, status=400)
#
#     db_data = shares.values('date', 'close')
#     df = pd.DataFrame.from_records(db_data)
#     df['date'] = pd.to_datetime(df['date'])
#     df['close'] = df['close'].astype(float)
#
#     # Расчёт EMA
#     df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()
#
#     # Расчёт RSI
#     delta = df['close'].diff()
#     gain = delta.clip(lower=0)
#     loss = -delta.clip(upper=0)
#     avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
#     rs = avg_gain / avg_loss
#     df['rsi'] = 100 - (100 / (1 + rs))
#     df.loc[:rsi_period-1, 'rsi'] = np.nan
#
#     # Бэктестинг
#     start_index = max(ema_period, rsi_period)
#     in_position = False
#     entry_price = 0.0
#     entry_date = None
#     trades = []
#     signals = []
#
#     for i in range(start_index, len(df)):
#         curr = df.iloc[i]
#         if pd.isna(curr.ema) or pd.isna(curr.rsi):
#             continue
#
#         if not in_position:
#             # Условие входа
#             if curr.close < curr.ema and curr.rsi < rsi_oversold:
#                 in_position = True
#                 entry_price = curr.close
#                 entry_date = curr.date
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'buy',
#                     'price': float(curr.close)
#                 })
#         else:
#             # Условия выхода
#             exit_signal = False
#             if curr.close > curr.ema:
#                 exit_signal = True
#             elif curr.rsi > rsi_overbought:
#                 exit_signal = True
#             elif curr.close <= entry_price * (1 - stop_loss_pct):
#                 exit_signal = True
#
#             if exit_signal:
#                 exit_price = curr.close
#                 ret = (exit_price - entry_price) / entry_price
#                 trades.append({
#                     "entry_date": entry_date.strftime('%Y-%m-%d'),
#                     "entry_price": float(entry_price),
#                     "exit_date": curr.date.strftime('%Y-%m-%d'),
#                     "exit_price": float(exit_price),
#                     "type": "long",
#                     "return_pct": float(ret)
#                 })
#                 signals.append({
#                     'date': curr.date.strftime('%Y-%m-%d'),
#                     'type': 'sell',
#                     'price': float(exit_price)
#                 })
#                 in_position = False
#
#     # Если позиция осталась открытой до конца данных – принудительно закрываем
#     if in_position:
#         exit_price = df.iloc[-1]['close']
#         exit_date = df.iloc[-1]['date']
#         ret = (exit_price - entry_price) / entry_price
#         trades.append({
#             "entry_date": entry_date.strftime('%Y-%m-%d'),
#             "entry_price": float(entry_price),
#             "exit_date": exit_date.strftime('%Y-%m-%d'),
#             "exit_price": float(exit_price),
#             "type": "long",
#             "return_pct": float(ret)
#         })
#         signals.append({
#             'date': exit_date.strftime('%Y-%m-%d'),
#             'type': 'sell',
#             'price': float(exit_price)
#         })
#
#     # --- Расширенная статистика ---
#
#     # 1. Общие данные
#     total_trades = len(trades)
#     winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
#     losing_trades = total_trades - winning_trades
#     win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
#
#     # 2. Абсолютная и относительная прибыль/убыток стратегии
#     final_capital = initial_capital
#     for t in trades:
#         final_capital *= (1 + t['return_pct'])
#     strategy_abs_profit = final_capital - initial_capital
#     strategy_return_pct = (final_capital / initial_capital - 1)
#
#     # 3. Число календарных дней
#     first_date = df['date'].iloc[0]
#     last_date = df['date'].iloc[-1]
#     calendar_days = (last_date - first_date).days + 1
#
#     # 4. Годовая доходность стратегии (по календарным дням)
#     if calendar_days > 0 and strategy_return_pct > -1:
#         annual_return_strategy = (1 + strategy_return_pct) ** (365 / calendar_days) - 1
#     else:
#         annual_return_strategy = None
#
#     # 5. Показатели для стратегии "купи и держи"
#     buy_hold_return_pct = (df['close'].iloc[-1] / df['close'].iloc[0] - 1)
#     buy_hold_abs_profit = buy_hold_return_pct * initial_capital
#     if calendar_days > 0 and buy_hold_return_pct > -1:
#         annual_return_buy_hold = (1 + buy_hold_return_pct) ** (365 / calendar_days) - 1
#     else:
#         annual_return_buy_hold = None
#
#     # 6. Максимальное снижение баланса относительно начальных инвестиций
#     equity = [initial_capital]
#     for t in trades:
#         equity.append(equity[-1] * (1 + t['return_pct']))
#     equity_series = pd.Series(equity)
#     drawdown_from_initial = (equity_series / initial_capital - 1).min()
#     max_drawdown_abs = abs(drawdown_from_initial) if drawdown_from_initial < 0 else 0
#
#     # 7. Средняя прибыль и средний убыток (в процентах)
#     profit_returns = [t['return_pct'] for t in trades if t['return_pct'] > 0]
#     loss_returns = [t['return_pct'] for t in trades if t['return_pct'] < 0]
#     avg_profit_pct = (sum(profit_returns) / len(profit_returns)) if profit_returns else 0
#     avg_loss_pct = (sum(loss_returns) / len(loss_returns)) if loss_returns else 0
#
#     # 8. Максимальная прибыль и максимальный убыток по одной сделке
#     max_profit_pct = max(profit_returns) if profit_returns else 0
#     max_loss_pct = min(loss_returns) if loss_returns else 0
#
#     # 9. Profit/Loss Index
#     total_profit = sum(profit_returns)   # суммарная прибыль в долях
#     total_loss = abs(sum(loss_returns))  # суммарный убыток в долях
#     if total_profit + total_loss > 0:
#         pl_index = ((total_profit - total_loss) / (total_profit + total_loss)) * 100
#     else:
#         pl_index = 0
#
#     # Формируем ответ
#     response_data = {
#         "status": "success",
#         "trades": trades,
#         "signals": signals,
#         "statistics": {
#             # Основные
#             "total_trades": total_trades,
#             "winning_trades": winning_trades,
#             "losing_trades": losing_trades,
#             "win_rate": round(win_rate, 2),
#
#             # Прибыль/убыток стратегии
#             "strategy_abs_profit": round(strategy_abs_profit, 2),
#             "strategy_return_pct": round(strategy_return_pct * 100, 2),
#             "strategy_annual_return_pct": round(annual_return_strategy * 100, 2) if annual_return_strategy is not None else None,
#
#             # Прибыль/убыток "купи и держи"
#             "buy_hold_abs_profit": round(buy_hold_abs_profit, 2),
#             "buy_hold_return_pct": round(buy_hold_return_pct * 100, 2),
#             "buy_hold_annual_return_pct": round(annual_return_buy_hold * 100, 2) if annual_return_buy_hold is not None else None,
#
#             # Риск и просадки
#             "max_drawdown_from_initial_pct": round(max_drawdown_abs * 100, 2),  # % от начального капитала
#             "max_drawdown": round(max_drawdown_abs * 100, 2),  # для совместимости
#
#             # Статистика по сделкам
#             "avg_profit_pct": round(avg_profit_pct * 100, 2),
#             "avg_loss_pct": round(avg_loss_pct * 100, 2),
#             "max_profit_pct": round(max_profit_pct * 100, 2),
#             "max_loss_pct": round(max_loss_pct * 100, 2),
#
#             # Profit/Loss Index
#             "pl_index": round(pl_index, 2),
#
#             # Дополнительно
#             "calendar_days": calendar_days,
#             "initial_capital": initial_capital,
#             "final_capital": round(final_capital, 2),
#         }
#     }
#     return Response(response_data)

@api_view(['POST'])
@csrf_exempt
def strategy_test(request):
    # Параметры стратегии
    filename = request.data.get('filename')
    ema_period = int(request.data.get('ema_period', 20))                # n
    rsi_period = int(request.data.get('rsi_period', 14))                # m
    rsi_long_entry = int(request.data.get('rsi_long_entry', 30))        # α (oversold)
    rsi_long_exit  = int(request.data.get('rsi_long_exit', 50))         # β
    rsi_short_entry = int(request.data.get('rsi_short_entry', 70))      # γ (overbought)
    rsi_short_exit  = int(request.data.get('rsi_short_exit', 50))       # δ
    stop_loss_pct = float(request.data.get('stop_loss_pct', 0.05))       # s
    initial_capital = float(request.data.get('initial_capital', 10000))

    if not filename:
        return Response({"status": "error", "message": "Не указано имя файла"}, status=400)

    # Загрузка данных
    shares = Share.objects.filter(filename=filename).order_by('date')
    if not shares:
        return Response({"status": "error", "message": "Нет данных для файла"}, status=400)

    db_data = shares.values('date', 'close')
    df = pd.DataFrame.from_records(db_data)
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = df['close'].astype(float)

    # Расчёт EMA
    df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()

    # Расчёт RSI
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
    avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[:rsi_period-1, 'rsi'] = np.nan

    # Бэктестинг
    start_index = max(ema_period, rsi_period)
    in_position = False
    position_type = None
    entry_price = 0.0
    entry_date = None
    trades = []
    signals = []

    for i in range(start_index, len(df)):
        curr = df.iloc[i]
        if pd.isna(curr.ema) or pd.isna(curr.rsi):
            continue

        if not in_position:
            long_condition = (curr.close < curr.ema) and (curr.rsi < rsi_long_entry)
            short_condition = (curr.close > curr.ema) and (curr.rsi > rsi_short_entry)

            if long_condition:
                in_position = True
                position_type = 'long'
                entry_price = curr.close
                entry_date = curr.date
                signals.append({
                    'date': curr.date.strftime('%Y-%m-%d'),
                    'type': 'buy',
                    'price': float(curr.close)
                })
            elif short_condition:
                in_position = True
                position_type = 'short'
                entry_price = curr.close
                entry_date = curr.date
                signals.append({
                    'date': curr.date.strftime('%Y-%m-%d'),
                    'type': 'short',
                    'price': float(curr.close)
                })

        else:
            exit_signal = False
            exit_reason = None

            if position_type == 'long':
                if curr.close > curr.ema:
                    exit_signal = True
                    exit_reason = 'ema'
                elif curr.rsi > rsi_long_exit:
                    exit_signal = True
                    exit_reason = 'rsi_exit'
                elif curr.close <= entry_price * (1 - stop_loss_pct):
                    exit_signal = True
                    exit_reason = 'stop_loss'

                if exit_signal:
                    exit_price = curr.close
                    ret = (exit_price - entry_price) / entry_price
                    trades.append({
                        "entry_date": entry_date.strftime('%Y-%m-%d'),
                        "entry_price": float(entry_price),
                        "exit_date": curr.date.strftime('%Y-%m-%d'),
                        "exit_price": float(exit_price),
                        "type": "long",
                        "return_pct": float(ret),
                        "exit_reason": exit_reason
                    })
                    signals.append({
                        'date': curr.date.strftime('%Y-%m-%d'),
                        'type': 'sell',
                        'price': float(exit_price)
                    })
                    in_position = False

            elif position_type == 'short':
                if curr.close < curr.ema:
                    exit_signal = True
                    exit_reason = 'ema'
                elif curr.rsi < rsi_short_exit:
                    exit_signal = True
                    exit_reason = 'rsi_exit'
                elif curr.close >= entry_price * (1 + stop_loss_pct):
                    exit_signal = True
                    exit_reason = 'stop_loss'

                if exit_signal:
                    exit_price = curr.close
                    ret = (entry_price - exit_price) / entry_price
                    trades.append({
                        "entry_date": entry_date.strftime('%Y-%m-%d'),
                        "entry_price": float(entry_price),
                        "exit_date": curr.date.strftime('%Y-%m-%d'),
                        "exit_price": float(exit_price),
                        "type": "short",
                        "return_pct": float(ret),
                        "exit_reason": exit_reason
                    })
                    signals.append({
                        'date': curr.date.strftime('%Y-%m-%d'),
                        'type': 'cover',
                        'price': float(exit_price)
                    })
                    in_position = False

    # Принудительное закрытие позиции в конце данных
    if in_position:
        exit_price = df.iloc[-1]['close']
        exit_date = df.iloc[-1]['date']
        if position_type == 'long':
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        trades.append({
            "entry_date": entry_date.strftime('%Y-%m-%d'),
            "entry_price": float(entry_price),
            "exit_date": exit_date.strftime('%Y-%m-%d'),
            "exit_price": float(exit_price),
            "type": position_type,
            "return_pct": float(ret),
            "exit_reason": "end_of_data"
        })
        signals.append({
            'date': exit_date.strftime('%Y-%m-%d'),
            'type': 'sell' if position_type == 'long' else 'cover',
            'price': float(exit_price)
        })

    # --- Расширенная статистика ---

    # 1. Общие данные
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # 2. Абсолютная и относительная прибыль/убыток стратегии
    final_capital = initial_capital
    for t in trades:
        final_capital *= (1 + t['return_pct'])
    strategy_abs_profit = final_capital - initial_capital
    strategy_return_pct = (final_capital / initial_capital - 1)   # total_return

    # 3. Число календарных дней
    first_date = df['date'].iloc[0]
    last_date = df['date'].iloc[-1]
    calendar_days = (last_date - first_date).days + 1

    # 4. Годовая доходность стратегии (по календарным дням)
    if calendar_days > 0 and strategy_return_pct > -1:
        annual_return_strategy = (1 + strategy_return_pct) ** (365 / calendar_days) - 1
    else:
        annual_return_strategy = None

    # 5. Показатели для стратегии "купи и держи"
    buy_hold_return_pct = (df['close'].iloc[-1] / df['close'].iloc[0] - 1)
    buy_hold_abs_profit = buy_hold_return_pct * initial_capital
    if calendar_days > 0 and buy_hold_return_pct > -1:
        annual_return_buy_hold = (1 + buy_hold_return_pct) ** (365 / calendar_days) - 1
    else:
        annual_return_buy_hold = None

    # 6. Максимальное снижение баланса относительно начальных инвестиций
    #    (минимальное значение equity / initial_capital - 1)
    equity = [initial_capital]
    for t in trades:
        equity.append(equity[-1] * (1 + t['return_pct']))
    equity_series = pd.Series(equity)
    drawdown_from_initial = (equity_series / initial_capital - 1).min()
    max_drawdown_abs = abs(drawdown_from_initial) if drawdown_from_initial < 0 else 0

    # 7. Средняя прибыль и средний убыток (в процентах)
    profit_returns = [t['return_pct'] for t in trades if t['return_pct'] > 0]
    loss_returns = [t['return_pct'] for t in trades if t['return_pct'] < 0]
    avg_profit_pct = (sum(profit_returns) / len(profit_returns)) if profit_returns else 0
    avg_loss_pct = (sum(loss_returns) / len(loss_returns)) if loss_returns else 0

    # 8. Максимальная прибыль и максимальный убыток по одной сделке
    max_profit_pct = max(profit_returns) if profit_returns else 0
    max_loss_pct = min(loss_returns) if loss_returns else 0

    # 9. Profit/Loss Index
    total_profit = sum(profit_returns)   # суммарная прибыль в долях
    total_loss = abs(sum(loss_returns))  # суммарный убыток в долях (абсолютное значение)
    if total_profit + total_loss > 0:
        pl_index = ((total_profit - total_loss) / (total_profit + total_loss)) * 100
    else:
        pl_index = 0

    # Формируем ответ
    response_data = {
        "status": "success",
        "trades": trades,
        "signals": signals,
        "statistics": {
            # Основные
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),

            # Прибыль/убыток стратегии
            "strategy_abs_profit": round(strategy_abs_profit, 2),
            "strategy_return_pct": round(strategy_return_pct * 100, 2),
            "strategy_annual_return_pct": round(annual_return_strategy * 100, 2) if annual_return_strategy is not None else None,

            # Прибыль/убыток "купи и держи"
            "buy_hold_abs_profit": round(buy_hold_abs_profit, 2),
            "buy_hold_return_pct": round(buy_hold_return_pct * 100, 2),
            "buy_hold_annual_return_pct": round(annual_return_buy_hold * 100, 2) if annual_return_buy_hold is not None else None,

            # Риск и просадки
            "max_drawdown_from_initial_pct": round(max_drawdown_abs * 100, 2),  # % от начального капитала
            "max_drawdown": round(max_drawdown_abs * 100, 2),  # для совместимости

            # Статистика по сделкам
            "avg_profit_pct": round(avg_profit_pct * 100, 2),
            "avg_loss_pct": round(avg_loss_pct * 100, 2),
            "max_profit_pct": round(max_profit_pct * 100, 2),
            "max_loss_pct": round(max_loss_pct * 100, 2),

            # Profit/Loss Index
            "pl_index": round(pl_index, 2),

            # Дополнительно
            "calendar_days": calendar_days,
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
        }
    }
    return Response(response_data)