# Playbook de refatoração

Os exemplos são esquemáticos. Preserve nomes, contratos e stack do projeto real.

### Transformação 1: Segredo fixo para configuração externa
**Antes**
```python
app.config['SECRET_KEY'] = 'fixa'
```
**Depois**
```python
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
```

### Transformação 2: SQL concatenado para parâmetros
**Antes**
```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```
**Depois**
```python
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
```

### Transformação 3: Rota com regra de negócio para controller
**Antes**
```javascript
app.post('/orders', async (req, res) => { /* valida, calcula e persiste */ });
```
**Depois**
```javascript
router.post('/orders', orderController.create);
// controller coordena; serviço de aplicação executa o caso de uso
```

### Transformação 4: God class para módulos coesos
**Antes**
```python
class App:
    def route_and_query_and_charge_and_report(self): ...
```
**Depois**
```python
class OrderController: ...
class OrderRepository: ...
class PaymentGateway: ...
```

### Transformação 5: Estado global para dependência explícita
**Antes**
```javascript
let db = globalDatabase;
```
**Depois**
```javascript
function createOrderController({ orderRepository }) { /* usa a dependência recebida */ }
```

### Transformação 6: Query N+1 para carregamento em lote
**Antes**
```python
for order in orders:
    items = Item.query.filter_by(order_id=order.id).all()
```
**Depois**
```python
items = Item.query.filter(Item.order_id.in_([order.id for order in orders])).all()
```

### Transformação 7: Validação copiada para schema comum
**Antes**
```python
if len(title) < 3: return error
# a mesma regra é copiada em create e update
```
**Depois**
```python
def validate_title(title):
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 200:
        raise ValidationError('Título inválido')
```

### Transformação 8: Exceção engolida para erro previsível
**Antes**
```python
try:
    save()
except:
    return {'error': 'Erro'}
```
**Depois**
```python
try:
    save()
except DatabaseError:
    logger.exception('Falha ao persistir entidade')
    raise PersistenceError() from None
```

### Transformação 9: API deprecated para API atual
**Antes**
```python
user = User.query.get(user_id)
```
**Depois**
```python
user = db.session.get(User, user_id)
```
Confirme a versão do ORM e teste a semântica de `None`/404 antes de trocar.

### Transformação 10: Constantes explícitas para magic values
**Antes**
```python
if priority > 5: ...
```
**Depois**
```python
MAX_PRIORITY = 5
if priority > MAX_PRIORITY: ...
```
