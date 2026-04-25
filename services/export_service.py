"""
services/export_service.py
──────────────────────────
Utility for exporting report data to CSV/Excel formats.
"""

import csv
import os
from datetime import datetime

class ExportService:

    @staticmethod
    def export_to_csv(data_list: list, headers: list, filename_prefix: str) -> str:
        """
        Exports a list of dicts to a CSV file.
        Returns the absolute path to the generated file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        # Store in current directory or a dedicated exports folder
        filepath = os.path.abspath(filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for row in data_list:
                    # Convert dict to list based on headers or provided order
                    if isinstance(row, dict):
                        writer.writerow([row.get(h.lower().replace(" ", "_"), "") for h in headers])
                    else:
                        writer.writerow(row)
                        
            return filepath
        except Exception as e:
            print(f"Export Error: {e}")
            return ""

    @staticmethod
    def export_dashboard_summary(stats: dict, insights: list) -> str:
        """Specific exporter for the dashboard overview."""
        headers = ["Metric", "Value", "Trend %"]
        data = []
        for key, info in stats.items():
            data.append([key.title(), info.get("value", 0), f"{info.get('trend', 0)}%"])
        
        return ExportService.export_to_csv(data, headers, "dashboard_summary")
