"""Airflow 3. Coletores em paralelo; falhas propagadas e registradas."""
import logging
from datetime import timedelta
import pendulum
from airflow.sdk import dag, task, Variable


def notify_failure(context):
    logging.error('PASSO_LIVRE_FALHA dag=%s task=%s run=%s; verificar logs da tarefa',
                  context['dag'].dag_id, context['task_instance'].task_id, context['run_id'])


@dag(dag_id='passo_livre_diario', schedule='0 9 * * *',
     start_date=pendulum.datetime(2026,11,17,tz='America/Sao_Paulo'), catchup=False,
     max_active_runs=1, default_args={'retries':2,'retry_delay':timedelta(minutes=2),'on_failure_callback':notify_failure},
     tags=['Passo Livre','GS','Big Data'])
def pipeline():
    @task
    def ibge():
        from bigdata.collect import collect_ibge
        return collect_ibge()

    @task
    def clima():
        from bigdata.collect import collect_weather
        return collect_weather()

    @task
    def sp156():
        from bigdata.collect import collect_sp156
        return collect_sp156()

    @task
    def sptrans_opcional():
        from bigdata.collect import collect_sptrans
        token=Variable.get('SPTRANS_TOKEN',default=None)
        if not token:
            return {'status':'nao_configurada','fonte':'sptrans'}
        return collect_sptrans(token)

    @task
    def conferir_chegada(a,b,c,optional):
        from bigdata.collect import verify
        manifests=[a,b,c]+([optional] if 'arquivo' in optional else [])
        result=verify(manifests)
        logging.info('PASSO_LIVRE_COLETA_CONCLUIDA %s',result)
        return result

    conferir_chegada(ibge(),clima(),sp156(),sptrans_opcional())

pipeline()
