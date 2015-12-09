import json

import web

from persist import saveSmartThingDataPoint


urls = (
  "/", "index"
)
app = web.application(urls, globals())
render = web.template.render("templates/")

class index:
  def GET(self):
    return render.layout(
      render.index()
    )


  def POST(self):
    data = json.loads(web.data())
    saveSmartThingDataPoint(data)
    return json.dumps({"result": "success"})


if __name__ == "__main__":
  app.run()