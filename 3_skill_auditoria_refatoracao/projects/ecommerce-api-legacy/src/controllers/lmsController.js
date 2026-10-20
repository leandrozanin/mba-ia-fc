function createLmsController(repository) {
  return {
    checkout: async (req,res,next) => {
      try {
        const {usr:name,eml:email,pwd:password,c_id:courseId,card}=req.body||{};
        if(!name||!email||!password||!courseId||!card) return res.status(400).send('Bad Request');
        if(!/^\S+@\S+\.\S+$/.test(email)||!/^\d{12,19}$/.test(String(card))) return res.status(400).send('Bad Request');
        const result=await repository.checkout({name,email,password,courseId,card});
        if(result.notFound) return res.status(404).send('Curso nao encontrado');
        if(result.denied) return res.status(400).send('Pagamento recusado');
        return res.status(200).json({msg:'Sucesso',...result});
      } catch(error){return next(error);}
    },
    financialReport: async (req,res,next) => { try{return res.json(await repository.financialReport());}catch(error){return next(error);} },
    deleteUser: async (req,res,next) => { try {const deleted=await repository.deleteUser(req.params.id);return deleted?res.send('Usuario deletado com matriculas e pagamentos associados.'):res.status(404).send('Usuario nao encontrado');}catch(error){return next(error);} },
  };
}
module.exports={createLmsController};
