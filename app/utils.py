import io
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import cast, Float
import app.database.requests as rq


async def generate_excel_report(days=2):
    """Генерирует Excel отчет с данными за последние N дней"""
    
    # Получаем данные из БД
    records = await rq.get_recent_work_info(days)
    
    if not records:
        return None
    
    # Преобразуем данные в DataFrame
    data = []
    for record in records:
        data.append({
            'ID': record.id,
            'ID сотрудника': record.user_id,
            'ФИО': record.fullname or 'Не указано',
            'Организация': record.org_name,
            'Часы': record.hours,
            'Описание работы': record.work_description,
            'Дата': record.date.strftime('%d.%m.%Y %H:%M'),
        })
    
    df = pd.DataFrame(data)
    
    # Создаем Excel файл в памяти
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Лист с детализацией
        df.to_excel(writer, sheet_name='Детализация', index=False)
        
        # Автоматически подгоняем ширину колонок
        worksheet = writer.sheets['Детализация']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Лист со статистикой
        stats = await rq.get_work_statistics(days)
        stats_data = []
        for stat in stats:
            stats_data.append({
                'ФИО': stat.fullname or 'Не указано',
                'Количество записей': stat.records_count,
                'Сумма часов': stat.total_hours or 0,
            })
        
        if stats_data:
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='Статистика', index=False)
            
            # Автоподгонка ширины для статистики
            worksheet = writer.sheets['Статистика']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output


async def generate_text_report(days=2):
    """Генерирует текстовый отчет"""
    records = await rq.get_recent_work_info(days)
    
    if not records:
        return "📭 За последние {} дней записей не найдено.".format(days)
    
    report_lines = [
        "📊 *ОТЧЕТ О РАБОТЕ СОТРУДНИКОВ*",
        f"📅 Период: последние {days} дней",
        f"📋 Всего записей: {len(records)}",
        "=" * 40 + "\n"
    ]
    
    current_user = None
    user_records_count = 0
    
    for record in records:
        if current_user != record.fullname:
            if current_user:
                report_lines.append(f"📊 Итого у сотрудника: {user_records_count} записей\n")
                user_records_count = 0
            
            current_user = record.fullname
            report_lines.append(f"👤 *{record.fullname or 'Не указано'}* (ID: {record.user_id})")
            report_lines.append("-" * 30)
        
        report_lines.append(
            f"📅 {record.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"🏢 Организация: {record.org_name}\n"
            f"⏰ Часы: {record.hours}\n"
            f"📝 Описание: {record.work_description[:100]}..."
            f"{' (обрезано)' if len(record.work_description) > 100 else ''}\n"
        )
        user_records_count += 1
    
    if current_user:
        report_lines.append(f"📊 Итого у сотрудника: {user_records_count} записей")
    
    # Статистика
    stats = await rq.get_work_statistics(days)
    if stats:
        report_lines.append("\n" + "=" * 40)
        report_lines.append("📈 *СТАТИСТИКА ПО СОТРУДНИКАМ*")
        for stat in stats:
            report_lines.append(
                f"👤 {stat.fullname}: {stat.records_count} записей, "
                f"всего часов: {stat.total_hours or 0}"
            )
    
    return "\n".join(report_lines)