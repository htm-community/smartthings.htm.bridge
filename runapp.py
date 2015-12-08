import os
import json

import web

urls = (
  "/", "index"
)

class index:
  def POST(self):
    data = json.loads(web.data())
    print data


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8080))
  app = web.application(urls, globals())
  app.run()