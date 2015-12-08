import json

import web

urls = (
  "/", "index"
)

class index:
  def POST(self):
    data = json.loads(web.data())
    print data
    return json.dumps({"result": "success"})


if __name__ == "__main__":
  app = web.application(urls, globals())
  app.run()