const express=require('express');
const {createLmsController}=require('../controllers/lmsController');
function registerRoutes(app,repository){
  const router=express.Router();
  const controller=createLmsController(repository);
  router.post('/checkout',controller.checkout);
  router.get('/admin/financial-report',controller.financialReport);
  router.delete('/users/:id',controller.deleteUser);
  app.use('/api',router);
}
module.exports={registerRoutes};
