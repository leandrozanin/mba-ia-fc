const express=require('express');
const LmsRepository=require('./models/lmsRepository');
const {registerRoutes}=require('./views/routes');
const {config}=require('./utils');
function createApp(repository=new LmsRepository()){
  const app=express();
  app.use(express.json({limit:'32kb'}));
  repository.init();
  registerRoutes(app,repository);
  app.use((err,req,res,next)=>{if(res.headersSent)return next(err);return res.status(500).json({error:'Internal server error'});});
  return app;
}
if(require.main===module){createApp().listen(config.port,()=>console.log(`LMS API listening on ${config.port}`));}
module.exports={createApp};
