import tornado.web
import tornado.options
import tornado.ioloop
import logic
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from threading import Thread
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=False,
)

class TemplateRendering:
    def render_template(self, template_name, variables):
        env = Environment(loader = FileSystemLoader(settings['template_path']))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        content = template.render(variables)
        return content

class Application(tornado.web.Application):
    def __init__(self, mainT):
        handlers = [
            (r"/", MainHandler, {'mainT':mainT}),
            (r"/login", LoginHandler, {'mainT':mainT}),
            (r"/Alerts", AlertsHandler, {'mainT':mainT}),
            (r"/Alerts/([0-9])/(.*)", AlertsHandler, {'mainT':mainT}),
            (r"/alertinfo", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/alertinfo/([0-9])", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/Feed/(.*)", FeedHandler, {'mainT':mainT}),
            (r"/Feed", FeedHandler, {'mainT':mainT}),
            (r"/preview", PreviewHandler, {'mainT':mainT}),
            (r"/newTweets", NewTweetsHandler, {'mainT':mainT}),
            (r"/newTweets/(.*)", NewTweetsHandler, {'mainT':mainT}),
            (r'/(.*)', tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, mainT):
        self.mainT = mainT

class MainHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'index.html'
        variables = {
            'title' : "Watchtower"
        }
        content = self.render_template(template, variables)
        self.write(content)

class LoginHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'login.html'
        variables = {
            'title' : "Login Page"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self):
        userinfo = {
            'username': self.get_argument("username"),
            'password': self.get_argument("password")
        }
        if logic.login(userinfo):
            self.redirect("/Alerts")
        else:
            self.write("Information is not correct")

class AlertsHandler(BaseHandler, TemplateRendering):
    def get(self, alertid = None, posttype = None):
        logic.refrestAlertStatus(self.mainT)
        template = 'afterlogintemplate.html'
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(),
            'type' : "alertlist"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self, alertid = None, posttype= None):
        if posttype == 'remove':
            logic.deleteAlert(alertid, self.mainT)
        elif posttype == "stop":
            logic.stopAlert(alertid, self.mainT)
        else:
            logic.startAlert(alertid, self.mainT)
        self.redirect("/Alerts")

class CreateEditAlertsHandler(BaseHandler, TemplateRendering):
    def get(self, alertid = None):
        template = 'afterlogintemplate.html'
        variables = {}
        if alertid != None:
            variables['title'] = "Edit Alert"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "editAlert"
        else:
            variables['title'] = "Create Alert"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "createAlert"
        content = self.render_template(template, variables)
        self.write(content)

    def post(self, alertid = None):
        alert = {}
        alert['keywords'] = ",".join(self.get_argument("keywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = ",".join(self.request.arguments.get("languages"))
        else:
            alert['lang'] = ""
        if alertid != None:
            alert['id'] = alertid
            logic.updateAlert(alert, self.mainT)
        else:
            alert['name'] = self.get_argument('alertname')
            logic.addAlert(alert, self.mainT)
        self.redirect("/Alerts")

class PreviewHandler(BaseHandler, TemplateRendering):
    def post(self):
        template = 'tweetsTemplate.html'
        keywords = self.get_argument("keywords")
        print keywords
        languages = self.get_argument("languages")
        print languages
        variables = {
            'tweets': logic.searchTweets(keywords, languages)
        }
        content = self.render_template(template, variables)
        self.write(content)

class FeedHandler(BaseHandler, TemplateRendering):
    def get(self, scroll = None):
        template = 'afterlogintemplate.html'
        variables = {
            'title': "Feed",
            'alerts': logic.getAlertList(),
            'type': "feed"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self, scroll=None):
        if scroll is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            lastTweetId = self.get_argument('lastTweetId')
            variables = {
                'tweets': logic.getSkipTweets(alertid, lastTweetId)
            }
        else:
            template = 'alertFeed.html'
            alertid = self.get_argument('alertid')
            variables = {
                'tweets': logic.getTweets(alertid),
                'alertid': alertid
            }
        content = self.render_template(template, variables)
        self.write(content)

class NewTweetsHandler(BaseHandler, TemplateRendering):
    def post(self, get = None):
        if get is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            variables = {
                'tweets': logic.getNewTweets(alertid, newestId)
            }
            content = self.render_template(template, variables)
        else:
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            content = str(logic.checkTweets(alertid, newestId))
        self.write(content)

def main(mainT):
    tornado.options.parse_command_line()
    app = Application(mainT)
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()

def webserverInit(mainT):
    thr = Thread(target= main, args= [mainT] )
    thr.daemon = True
    thr.start()
    thr.join()

if __name__ == "__main__":
    main()
