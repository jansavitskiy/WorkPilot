import io
import os
import csv
from datetime import datetime
from pathlib import Path
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


ORG_FILE = "organizations.csv"


class SimpleOrgManager:
    """Простой менеджер организаций"""
    
    def __init__(self):
        # Создаем файл если нет
        try:
            with open(ORG_FILE, 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            with open(ORG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Название', 'Дата добавления'])
    

    def get_all_orgs(self):
        """Получить все организации"""
        orgs = []
        try:
            with open(ORG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Пропустить заголовок
                for row in reader:
                    if row:  # Если строка не пустая
                        orgs.append(row[0])  # Только название
        except:
            pass
        return orgs
    

    def add_org(self, name):
        """Добавить организацию"""
        try:
            with open(ORG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    name.strip(),
                    datetime.now().strftime("%d.%m.%Y %H:%M")
                ])
            return True
        except:
            return False
    

    def delete_org(self, name):
        """Удалить организацию по названию"""
        try:
            orgs = []
            with open(ORG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                for row in reader:
                    if row and row[0].lower() != name.lower():
                        orgs.append(row)
            
            with open(ORG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(orgs)
            return True
        except:
            return False
    

    def export_excel(self):
        """Экспорт в Excel"""
        orgs = self.get_all_orgs()
        if not orgs:
            return None
        
        # Простой DataFrame
        df = pd.DataFrame({'Организации': orgs})
        
        # В память
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return output


# Глобальный экземпляр
orgs = SimpleOrgManager()


class EnhancedOrgManager(SimpleOrgManager):
    """Расширенный менеджер организаций для работы с сотрудниками"""
    
    def __init__(self):
        super().__init__()
        self.org_file = Path(ORG_FILE)
    
    def get_excel_file(self):
        """Получить Excel файл для отправки"""
        excel_bytes = self.export_excel()
        if not excel_bytes:
            return None
        
        # Сохраняем временный файл
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        
        filename = f"organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = temp_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(excel_bytes.getvalue())
        
        return filepath
    
    def check_and_add_org(self, name, added_by="Сотрудник"):
        """Проверить и добавить организацию (с проверкой дубликатов)"""
        existing_orgs = self.get_all_orgs()
        name = name.strip()
        
        # Проверяем, существует ли уже
        if any(org.lower() == name.lower() for org in existing_orgs):
            return False, "Такая организация уже существует"
        
        # Добавляем с дополнительной информацией
        try:
            with open(ORG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    name,
                    datetime.now().strftime("%d.%m.%Y %H:%M"),
                    added_by
                ])
            return True, "Организация успешно добавлена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def get_formatted_list(self, limit=None):
        """Получить форматированный список организаций"""
        orgs = self.get_all_orgs()
        if not orgs:
            return "📭 Список организаций пуст"
        
        if limit and len(orgs) > limit:
            shown = orgs[:limit]
            text = "📋 *Список организаций* (первые {}):\n\n".format(limit)
            text += "\n".join([f"• {org}" for org in shown])
            text += f"\n\n... и еще {len(orgs) - limit} организаций"
        else:
            text = "📋 *Список организаций* (всего {}):\n\n".format(len(orgs))
            text += "\n".join([f"• {org}" for org in orgs])
        
        return text
    
    def cleanup_temp_files(self, max_age_hours=24):
        """Очистить старые временные файлы"""
        temp_dir = Path("temp_files")
        if not temp_dir.exists():
            return
        
        now = datetime.now()
        for file in temp_dir.glob("*.xlsx"):
            try:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if (now - file_time).total_seconds() > max_age_hours * 3600:
                    file.unlink()
            except:
                continue


# Создаем экземпляр расширенного менеджера
org_manager = EnhancedOrgManager()


# Дополнительная функция для отправки файла
def get_organizations_file():
    """Получить файл с организациями для отправки"""
    return org_manager.get_excel_file()
