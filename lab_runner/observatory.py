"""Run the 3D Observatory against an owned, authenticated integration-lab stack."""
import base64
import hashlib
import re
from pathlib import Path

from .stack import ROOT


class ObservatoryShell:
    """Public static graphics; all run/conversation reads retain the Lab guard."""
    def __init__(self, app, directory):
        from starlette.middleware.exceptions import ExceptionMiddleware
        from starlette.staticfiles import StaticFiles
        self.app = app
        self.files = ExceptionMiddleware(StaticFiles(directory=directory,html=True))
        page = (Path(directory)/'index.html').read_text()
        inline = re.search(r'<script type="importmap">(.*?)</script>',page).group(1)
        digest = base64.b64encode(hashlib.sha256(inline.encode()).digest()).decode()
        self.csp = ("default-src 'none'; script-src 'self' 'sha256-"+digest+
            "'; style-src 'self'; font-src 'self'; img-src 'self' blob: data:; "
            "connect-src 'self' blob:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")

    async def __call__(self,scope,receive,send):
        path = scope.get('path','')
        if scope['type']=='http' and scope['method'] in {'GET','HEAD'} and path=='/observatory':
            from starlette.responses import RedirectResponse
            return await RedirectResponse('/observatory/')(scope,receive,send)
        if (scope['type']=='http' and scope['method'] in {'GET','HEAD'} and
                path.startswith('/observatory/') and
                not any(part.startswith('.') for part in path.split('/') if part)):
            child = {**scope,'root_path':'','path':path[len('/observatory'):],
                     'raw_path':path[len('/observatory'):].encode()}
            async def headers(message):
                if message['type']=='http.response.start':
                    message={**message,'headers':list(message.get('headers',[]))+[
                        (b'cache-control',b'no-store'),(b'referrer-policy',b'no-referrer'),
                        (b'x-content-type-options',b'nosniff'),
                        (b'content-security-policy',self.csp.encode())]}
                await send(message)
            return await self.files(child,receive,headers)
        return await self.app(scope,receive,send)


def application():
    from prosaic_integration_lab.app import create_app
    from prosaic_integration_lab.run_observations import RunObservations
    return ObservatoryShell(create_app(observations=RunObservations()),
        ROOT/'prototypes'/'observatory')


def main(argv=None):
    from .chat import main as chat_main
    return chat_main(argv,application_factory=application,landing_path='/observatory/')


if __name__=='__main__':
    raise SystemExit(main())
