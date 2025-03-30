from asyncio import sleep

from anycaptcha import Solver, Service
from loguru import logger

from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient


class CaptchaSolver(RequestClient):
    def __init__(self, api_key: str, proxy: Proxy | None):
        self.solver = Solver(Service.TWOCAPTCHA, api_key=api_key)

        self.api_key = api_key

        super().__init__(proxy=proxy)

    async def solve_captcha(self, page_url: str, site_key: str) -> str:
        logger.debug("Solving captcha...")
        async with self.solver as solver:
            solved = await solver.solve_recaptcha_v3(
                site_key=site_key,
                page_url=page_url,
            )
            token = solved.solution.token
            return token

    async def solve_galxe_captcha(self):
        logger.debug(f'Solving captcha...')
        task_id = await self.__create_task()
        return await self.__get_task_result(task_id)

    async def __get_task_result(self, task_id: int) -> tuple[str, str, str, str]:
        json_data = {
            'clientKey': self.api_key,
            'taskId': task_id
        }
        while True:
            response_json, status = await self.make_request(
                method="POST",
                url='https://api.2captcha.com/getTaskResult',
                json=json_data
            )
            try:
                if response_json['status'] == 'processing':
                    await sleep(5)
                    continue
                solution = response_json['solution']
                lot_number = solution['lot_number']
                captcha_output = solution['captcha_output']
                pass_token = solution['pass_token']
                gen_time = solution['gen_time']
                return lot_number, captcha_output, pass_token, gen_time
            except KeyError:
                await sleep(5)

    async def __create_task(self) -> int:
        json_data = {
            "clientKey": self.api_key,
            "task": {
                "type": "GeeTestTaskProxyless",
                "websiteURL": "https://app.galxe.com/",
                "version": 4,
                "initParameters": {
                    "captcha_id": "244bcb8b9846215df5af4c624a750db4"
                }
            }
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://api.2captcha.com/createTask',
            json=json_data
        )
        task_id = response_json['taskId']
        return task_id