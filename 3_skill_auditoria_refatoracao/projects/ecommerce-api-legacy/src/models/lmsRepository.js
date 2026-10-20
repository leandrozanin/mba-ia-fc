const sqlite3 = require('sqlite3').verbose();
const { hashPassword } = require('../utils');

class LmsRepository {
  constructor(db = new sqlite3.Database(':memory:')) { this.db = db; }
  init() {
    this.db.serialize(() => {
      this.db.run('PRAGMA foreign_keys = ON');
      this.db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT)');
      this.db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
      this.db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
      this.db.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
      this.db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
      this.db.run("INSERT INTO users (name,email,pass) VALUES ('Leonan','leonan@fullcycle.com.br',?)", [hashPassword('123')]);
      this.db.run("INSERT INTO courses (title,price,active) VALUES ('Clean Architecture',997.00,1),('Docker',497.00,1)");
      this.db.run("INSERT INTO enrollments (user_id,course_id) VALUES (1,1)");
      this.db.run("INSERT INTO payments (enrollment_id,amount,status) VALUES (1,997.00,'PAID')");
    });
  }
  run(sql, params=[]) { return new Promise((resolve,reject)=>this.db.run(sql,params,function(err){err?reject(err):resolve({lastID:this.lastID,changes:this.changes});})); }
  get(sql, params=[]) { return new Promise((resolve,reject)=>this.db.get(sql,params,(err,row)=>err?reject(err):resolve(row))); }
  all(sql, params=[]) { return new Promise((resolve,reject)=>this.db.all(sql,params,(err,rows)=>err?reject(err):resolve(rows))); }
  async checkout({name,email,password,courseId,card}) {
    await this.run('BEGIN IMMEDIATE');
    try {
      const course=await this.get('SELECT * FROM courses WHERE id=? AND active=1',[courseId]);
      if(!course){await this.run('ROLLBACK'); return {notFound:true};}
      let user=await this.get('SELECT id FROM users WHERE email=?',[email]);
      if(!user){const created=await this.run('INSERT INTO users(name,email,pass) VALUES(?,?,?)',[name,email,hashPassword(password)]);user={id:created.lastID};}
      console.log(`Processing payment with card ending ${String(card).slice(-4)}`);
      const status=String(card).startsWith('4')?'PAID':'DENIED';
      if(status!=='PAID'){await this.run('ROLLBACK');return {denied:true};}
      const enrollment=await this.run('INSERT INTO enrollments(user_id,course_id) VALUES(?,?)',[user.id,courseId]);
      await this.run('INSERT INTO payments(enrollment_id,amount,status) VALUES(?,?,?)',[enrollment.lastID,course.price,status]);
      await this.run('INSERT INTO audit_logs(action,created_at) VALUES(?,datetime(\'now\'))',[`Checkout course ${courseId} by ${user.id}`]);
      await this.run('COMMIT');
      return {enrollment_id:enrollment.lastID};
    } catch(error) { await this.run('ROLLBACK'); throw error; }
  }
  async financialReport() {
    const rows=await this.all(`SELECT c.title AS course,e.id AS enrollment_id,u.name AS student,p.amount,p.status
      FROM courses c LEFT JOIN enrollments e ON e.course_id=c.id
      LEFT JOIN users u ON u.id=e.user_id LEFT JOIN payments p ON p.enrollment_id=e.id ORDER BY c.id,e.id`);
    const result=[]; let current;
    for(const row of rows){
      if(!current||current.course!==row.course){current={course:row.course,revenue:0,students:[]};result.push(current);}
      if(row.enrollment_id){if(row.status==='PAID')current.revenue+=row.amount||0;current.students.push({student:row.student||'Unknown',paid:row.amount||0});}
    }
    return result;
  }
  async deleteUser(id) {
    await this.run('BEGIN IMMEDIATE');
    try {
      await this.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id=?)',[id]);
      await this.run('DELETE FROM enrollments WHERE user_id=?',[id]);
      const result=await this.run('DELETE FROM users WHERE id=?',[id]);
      await this.run('COMMIT');
      return result.changes>0;
    } catch(error) { await this.run('ROLLBACK'); throw error; }
  }
}
module.exports=LmsRepository;
