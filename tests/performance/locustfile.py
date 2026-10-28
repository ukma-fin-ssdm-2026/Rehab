import logging

from locust import HttpUser, between, events, task

MAX_P95_MS = 500


class StatisticsUser(HttpUser):

    wait_time = between(1, 2)

    @task
    def load_statistics(self):
        """Надсилає авторизований запит до статистики."""
        self.client.get(
            "/api/v1/statistics",
            headers={"Authorization": "Bearer user-42"},
            name="Отримання статистики",
        )


@events.quitting.add_listener
def check_performance(environment, **kwargs):
    stats = environment.stats.total

    if stats.num_requests == 0:
        logging.error("Тест не виконав жодного запиту.")
        environment.process_exit_code = 1
        return

    p95 = stats.get_response_time_percentile(0.95)

    logging.info(
        "PERF-001: p95=%s мс, поріг=%s мс, запитів=%s, помилок=%s",
        p95,
        MAX_P95_MS,
        stats.num_requests,
        stats.num_failures,
    )

    if p95 > MAX_P95_MS or stats.num_failures > 0:
        logging.error("PERF-001: перевірку не пройдено.")
        environment.process_exit_code = 1
    else:
        logging.info("PERF-001: перевірку пройдено.")
        environment.process_exit_code = 0
