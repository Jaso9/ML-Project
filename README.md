# Flight Delay Prediction

ML-проект по прогнозированию задержки вылета пассажирского рейса на 15 и более минут.

**Датасет:** [US Flight Delays, Bureau of Transportation Statistics](https://www.kaggle.com/datasets/usdot/flight-delays).

## Методология и этапы исследования

- EDA и анализ пропусков, выбросов и корреляций.
- Данные разделены по времени: **Train — январь–сентябрь, Test — ноябрь–декабрь**.
- Для снижения вычислительной нагрузки использованы 15 наиболее загруженных аэропортов.
- Выполнен feature engineering: циклическое кодирование времени и месяца, признаки нагрузки аэропортов.
- Исключены признаки, которые становятся известны только после вылета.
- Реализована обработка числовых и категориальных признаков с помощью `Pipeline`, `SimpleImputer`, `StandardScaler` и `OneHotEncoder`.
- Использована временная кросс-валидация `TimeSeriesSplit`.
- Сравнены модели: Logistic Regression, Linear SVM, LightGBM и CatBoost.
- Для LightGBM и CatBoost выполнен подбор гиперпараметров с помощью [**Optuna**](https://optuna.org/).
- Реализован MLP на PyTorch.
- Проведены **ablation study**, blending и stacking.
- Дополнительно исследована стоимость ошибок `FP/FN` и влияние порога классификации.

## Результаты

На кросс-валидации лучшими по PR-AUC были LightGBM и CatBoost (около **0.324**).

На временной тестовой выборке:
- **SVM** — лучший PR-AUC: **0.2606**;
- **LightGBM** — лучший ROC-AUC: **0.6191**;
- **MLP** — PR-AUC около **0.2185**, уступила бустинговым моделям;
- stacking и blending не улучшили результаты отдельных моделей на test.

Отдельные эксперименты показали, что `SCHEDULED_TIME` оказался практически избыточным относительно `DISTANCE`, а добавление `TAIL_NUMBER` не дало устойчивого прироста качества.

## Структура

```text
.
├── FlightDelayPrediction.ipynb
├── flight_delay_prediction_report.pdf
├── README.md
└── requirements.txt
```
## Запуск

Для запуска ноутбука можно использовать Kaggle или Jupyter/Google Colab.

Установить зависимости:
```text
pip install -r requirements.txt
```
Датасет в репозиторий не включён, путь к нему в ноутбуке рассчитан на окружение Kaggle.
