from google.appengine.api import channel
from google.appengine.ext import deferred
import webapp2
from webapp2_extras import sessions_memcache
from webapp2_extras import sessions
from webapp2_extras import jinja2
import uuid

#Creates a session, sends the request, saves the session, uses jinja to render cache in app, loads into browser after being subitted.
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)

        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(name='mc_session',
            factory=sessions_memcache.MemcacheSessionFactory)

    @webapp2.cached_property
    def jinja2(self):
        j = jinja2.get_jinja2(app=self.app)
        pass
        return j

    def render_response(self, _template, **context):

        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)

class MainHandler(BaseHandler):

    def get(self):
        channel_token = self.session.get('channel_token')
        if channel_token is None:
            client_id = str(uuid.uuid4()).replace("-",'')
            channel_token = channel.create_channel(client_id)
            self.session['channel_token'] = channel_token
            self.session['client_id'] = client_id

        client_id = self.session['client_id']


        deferred.defer(channel.send_message,client_id,"This is the 2 second delayed message",_countdown=2)
        deferred.defer(channel.send_message,client_id,"This is the 10 second delayed message",_countdown=10)

        self.render_response('home.html',**{"token":channel_token,"client_id":client_id})


class Send_Message(BaseHandler):
    def get(self):
        self.render_response('message.html',**{'token':self.session['channel_token'],'client_id':self.session['client_id']})

    def post(self):
        message = self.request.get("message")

        client_id = self.session['client_id']
        channel.send_message(client_id,message)
        self.redirect('/message')


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '9upj9p80pi08hn09k9jk',
    }
app = webapp2.WSGIApplication([
    ('/', MainHandler) ,
    ('/message', Send_Message)
],
    debug=True, config=config)