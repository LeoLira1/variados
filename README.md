# 🌿 CAMDA Estoque - Mapa de Calor

Visualização estilo treemap do estoque da CAMDA Quirinópolis, com conferência física integrada.

## Como usar

### 1. Instalar
```bash
pip install -r requirements.txt
```

### 2. Rodar
```bash
streamlit run app.py
```

### 3. No celular
Após rodar, acesse o endereço exibido no terminal (ex: `http://192.168.x.x:8501`) pelo navegador do celular.

### 4. Fluxo diário
1. Exporte a planilha do BI (CAMDA BI - Estoque)
2. Abra o app e faça upload na aba "Atualizar Planilha"
3. Na aba **Contagem**, insira as quantidades físicas
4. O **Mapa** mostra verde (batendo) ou vermelho (divergente)
5. A aba **Divergências** lista tudo que não bateu

### Cores
- 🟢 **Verde** = Estoque físico bate com o sistema
- 🔴 **Vermelho** = Divergência (físico ≠ sistema)
- 🟡 **Amarelo** = Físico maior que sistema
- ⬜ **Cinza/padrão** = Ainda não conferido

### Dica
Use o botão "✅ Tudo bate" para marcar todos de uma categoria como OK, e depois ajuste só os que divergiram.
