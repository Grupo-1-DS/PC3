import json
import time
from datetime import datetime


class SagaMetrics:
    def __init__(self):
        self.data = {
            'total_sagas': 0,
            'succeeded': 0,
            'failed': 0,
            'compensated': 0,
            'total_retries': 0,
            'total_dlq_messages': 0,
            'execution_times': [],
            'compensation_times': [],
            'step_failures': {},
            'timestamp': datetime.now().isoformat()
        }

    def record_saga_start(self):
        """Registra el inicio de un nuevo SAGA"""
        self.data['total_sagas'] += 1

    def record_saga_success(self, execution_time):
        """Registra un SAGA exitoso"""
        self.data['succeeded'] += 1
        self.data['execution_times'].append(execution_time)

    def record_saga_failure(self, failed_step, execution_time):
        """Registra un SAGA fallido"""
        self.data['failed'] += 1
        self.data['compensated'] += 1
        self.data['execution_times'].append(execution_time)

        if failed_step not in self.data['step_failures']:
            self.data['step_failures'][failed_step] = 0
        self.data['step_failures'][failed_step] += 1

    def record_retry(self):
        """Registra un intento de retry"""
        self.data['total_retries'] += 1

    def record_dlq(self):
        """Registra un mensaje enviado al DLQ"""
        self.data['total_dlq_messages'] += 1

    def record_compensation_time(self, compensation_time):
        """Registra el tiempo de compensación"""
        self.data['compensation_times'].append(compensation_time)

    def get_report(self):
        """Genera un reporte con las métricas calculadas"""
        total_sagas = self.data['total_sagas']

        if total_sagas == 0:
            return {
                'total_sagas': 0,
                'success_rate': "0%",
                'compensation_rate': "0%",
                'avg_execution_time': "0s",
                'avg_retries_per_saga': "0",
                'total_dlq_messages': 0,
                'avg_compensation_time': "0s",
                'step_failures': {}
            }

        avg_time = sum(self.data['execution_times']) / len(
            self.data['execution_times']) if self.data['execution_times'] else 0
        avg_retries = self.data['total_retries'] / total_sagas
        compensation_rate = (self.data['compensated'] / total_sagas * 100)
        success_rate = (self.data['succeeded'] / total_sagas * 100)
        avg_comp_time = sum(self.data['compensation_times']) / len(
            self.data['compensation_times']) if self.data['compensation_times'] else 0

        return {
            'total_sagas': total_sagas,
            'success_rate': f"{success_rate:.2f}%",
            'compensation_rate': f"{compensation_rate:.2f}%",
            'avg_execution_time': f"{avg_time:.2f}s",
            'avg_retries_per_saga': f"{avg_retries:.2f}",
            'total_dlq_messages': self.data['total_dlq_messages'],
            'avg_compensation_time': f"{avg_comp_time:.2f}s",
            'step_failures': self.data['step_failures']
        }

    def save_to_file(self, filename='saga_metrics.json'):
        """Guarda el reporte en un archivo JSON"""
        with open(filename, 'w') as f:
            json.dump(self.get_report(), f, indent=2)
        print(f" Métricas guardadas en {filename}")

    def print_report(self):
        """Imprime el reporte de métricas en consola"""
        report = self.get_report()
        print("\n" + "="*60)
        print(" REPORTE DE MÉTRICAS SAGA")
        print("="*60)
        print(f"Total SAGAs ejecutados:       {report['total_sagas']}")
        print(f"Tasa de éxito:                {report['success_rate']}")
        print(f"Tasa de compensación:         {report['compensation_rate']}")
        print(f"Tiempo promedio ejecución:    {report['avg_execution_time']}")
        print(
            f"Tiempo promedio compensación: {report['avg_compensation_time']}")
        print(
            f"Reintentos promedio:          {report['avg_retries_per_saga']}")
        print(f"Mensajes en DLQ:              {report['total_dlq_messages']}")

        if report['step_failures']:
            print("\n Pasos que más fallan:")
            for step, count in report['step_failures'].items():
                percentage = (count / report['total_sagas']) * 100
                print(f"   - {step}: {count} veces ({percentage:.1f}%)")
        else:
            print("\n✅ Sin fallos en pasos")

        print("="*60 + "\n")

    def calculate_trends(self, previous_file='saga_metrics_previous.json'):
        """
        Calcula trends comparando con ejecución anterior
        Retorna dict con trend por métrica (mejora/empeora/igual)
        """
        import os

        if not os.path.exists(previous_file):
            return None

        try:
            with open(previous_file, 'r') as f:
                prev = json.load(f)
        except:
            return None

        current = self.get_report()
        trends = {}

        # Comparar tasa de éxito
        prev_success = float(prev.get('success_rate', '0%').replace('%', ''))
        curr_success = float(current['success_rate'].replace('%', ''))
        if curr_success > prev_success:
            trends['success_rate'] = 'mejora'
        elif curr_success < prev_success:
            trends['success_rate'] = 'empeora'
        else:
            trends['success_rate'] = 'igual'

        # Comparar reintentos (menos es mejor)
        prev_retries = float(prev.get('avg_retries_per_saga', '0'))
        curr_retries = float(current['avg_retries_per_saga'])
        if curr_retries < prev_retries:
            trends['retries'] = 'mejora'
        elif curr_retries > prev_retries:
            trends['retries'] = 'empeora'
        else:
            trends['retries'] = 'igual'

        return trends

    def get_resilience_report(self):
        """Genera informe específico de resiliencia"""
        total = self.data['total_sagas']
        if total == 0:
            return {}

        # Calcular tasa de recuperación (SAGAs que se compensaron correctamente)
        recovery_rate = (self.data['compensated'] / total * 100) if self.data['compensated'] > 0 else 0

        # MTTR aproximado (tiempo promedio de compensación)
        mttr = sum(self.data['compensation_times']) / len(self.data['compensation_times']) \
               if self.data['compensation_times'] else 0

        return {
            'total_failures': self.data['failed'],
            'recovery_rate': f"{recovery_rate:.2f}%",
            'mttr': f"{mttr:.2f}s",
            'dlq_messages': self.data['total_dlq_messages'],
            'avg_retries': f"{self.data['total_retries'] / total:.2f}"
        }

    def print_resilience_report(self):
        """Imprime informe de resiliencia con trends"""
        resilience = self.get_resilience_report()
        trends = self.calculate_trends()

        print("\n" + "="*60)
        print("🛡️  INFORME DE RESILIENCIA")
        print("="*60)
        print(f"Total de fallos:              {resilience.get('total_failures', 0)}")
        print(f"Tasa de recuperación:         {resilience.get('recovery_rate', '0%')}")
        print(f"MTTR (tiempo recuperación):   {resilience.get('mttr', '0s')}")
        print(f"Mensajes en DLQ:              {resilience.get('dlq_messages', 0)}")
        print(f"Reintentos promedio:          {resilience.get('avg_retries', '0')}")

        if trends:
            print("\n📊 Trends (comparado con ejecución anterior):")
            icons = {'mejora': '📈', 'empeora': '📉', 'igual': '➡️'}
            for metric, trend in trends.items():
                icon = icons.get(trend, '?')
                print(f"   {icon} {metric}: {trend}")

        print("="*60 + "\n")

    def save_with_history(self, filename='saga_metrics.json'):
        """Guarda métricas actuales y preserva las anteriores como historial"""
        import os
        import shutil

        # Si existe el archivo actual, guardarlo como "previous"
        if os.path.exists(filename):
            shutil.copy(filename, filename.replace('.json', '_previous.json'))

        # Guardar las nuevas métricas
        self.save_to_file(filename)

    def reset(self):
        """Reinicia todas las métricas"""
        self.__init__()


# Instancia global para usar en todo el proyecto
saga_metrics = SagaMetrics()
