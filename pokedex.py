import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk  # Para carregar e exibir imagens




# -----------------------------
# Função para conectar ao banco
# -----------------------------
def conectar():
    return sqlite3.connect("pokemon.db")




# -------------------------------------------------------
# Garante que a coluna 'imagem' exista na tabela pokemons
# Se a tabela foi criada em versão anterior sem 'imagem',
# adicionamos a coluna com ALTER TABLE.
# -------------------------------------------------------
def garantir_coluna_imagem():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("PRAGMA table_info(pokemons)")  # informações das colunas
    colunas = [row[1] for row in cursor.fetchall()]  # row[1] é o nome da coluna
    if "imagem" not in colunas:
        # Adiciona a coluna "imagem" caso esteja faltando
        cursor.execute("ALTER TABLE pokemons ADD COLUMN imagem TEXT")
        conexao.commit()
    conexao.close()




# ---------------------------------
# Criar tabela com coluna de imagem
# ---------------------------------
def criar_tabela():
    conexao = conectar()
    cursor = conexao.cursor()
    # Cria a tabela (se não existir)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemons (
        numero INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        descricao TEXT,
        peso REAL,
        altura REAL
        -- OBS: não adicionamos "imagem" aqui intencionalmente para manter compatibilidade
    )
    """)
    conexao.commit()
    conexao.close()


    # Depois de criar (ou confirmar existência), garantimos que a coluna imagem exista.
    # Isso cobre casos onde o banco foi criado por uma versão antiga do programa.
    garantir_coluna_imagem()




# ---------------------------------------------------------
# Converte string para float quando possível, senão None.
# Evita ValueError quando campos de peso/altura estiverem vazios.
# ---------------------------------------------------------
def parse_float_or_none(valor):
    if valor is None:
        return None
    v = str(valor).strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None




# ---------------------------------------------------------
# Função para inserir Pokémon (chamada pela interface GUI)
# ---------------------------------------------------------
def inserir_pokemon():
    numero = entry_numero.get().strip()
    nome = entry_nome.get().strip()
    tipo = entry_tipo.get().strip()
    descricao = entry_desc.get("1.0", tk.END).strip()
    peso = parse_float_or_none(entry_peso.get())
    altura = parse_float_or_none(entry_altura.get())
    imagem = entry_imagem.get().strip()


    # Validações básicas
    if not numero or not nome or not tipo:
        messagebox.showerror("Erro", "Número, Nome e Tipo são obrigatórios!")
        return


    conexao = conectar()
    cursor = conexao.cursor()
    try:
        # Insere permitindo peso/altura NULL caso não preenchidos
        cursor.execute(
            "INSERT INTO pokemons (numero, nome, tipo, descricao, peso, altura, imagem) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (int(numero), nome, tipo, descricao, peso, altura, imagem)
        )
        conexao.commit()
        messagebox.showinfo("Sucesso", f"Pokémon {nome} inserido com sucesso.")
        listar_pokemons()
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Já existe um Pokémon com esse número.")
    finally:
        conexao.close()




# ----------------------------------------------------
# Selecionar imagem do Pokémon pelo explorador de arquivos
# ----------------------------------------------------
def selecionar_imagem():
    caminho = filedialog.askopenfilename(
        title="Selecione a imagem do Pokémon",
        filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.gif")]
    )
    if caminho:
        entry_imagem.delete(0, tk.END)
        entry_imagem.insert(0, caminho)




# ------------------------------------------
# Listar todos os Pokémons no TreeView + Imagem
# Observação importante: aqui "padronizamos" cada linha
# para ter exatamente a mesma quantidade de colunas que o TreeView espera.
# ------------------------------------------
def listar_pokemons():
    for item in tree.get_children():
        tree.delete(item)


    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM pokemons")
    registros = cursor.fetchall()
    conexao.close()


    for linha in registros:
        # Converte tuple para lista mutável
        linha_list = list(linha)


        # Se a tabela antiga não tiver a coluna 'imagem', padronizamos com string vazia
        # 'colunas' é a tupla global de colunas que o Treeview espera
        if len(linha_list) < len(colunas):
            linha_list += [''] * (len(colunas) - len(linha_list))


        # Substitui None por '' para exibição no Treeview (evita "None")
        linha_display = ["" if v is None else v for v in linha_list]


        tree.insert("", tk.END, values=linha_display)




# -----------------------------------
# Mostrar imagem e preencher formulário ao selecionar
# Corrige uso de tree.selection() pegando o primeiro id corretamente
# -----------------------------------
def mostrar_imagem(event):
    selecionados = tree.selection()
    if not selecionados:
        return


    item_id = selecionados[0]  # pega o primeiro item selecionado (id)
    valores = tree.item(item_id, "values")


    # Padroniza o tamanho do tuple/lista para evitar index out of range
    valores_list = list(valores)
    if len(valores_list) < len(colunas):
        valores_list += [''] * (len(colunas) - len(valores_list))


    # Preenche o formulário com os dados selecionados (sempre usando índices válidos)
    entry_numero.delete(0, tk.END)
    entry_numero.insert(0, valores_list[0])
    entry_nome.delete(0, tk.END)
    entry_nome.insert(0, valores_list[1])
    entry_tipo.delete(0, tk.END)
    entry_tipo.insert(0, valores_list[2])
    entry_desc.delete("1.0", tk.END)
    entry_desc.insert("1.0", valores_list[3])
    entry_peso.delete(0, tk.END)
    entry_peso.insert(0, valores_list[4])
    entry_altura.delete(0, tk.END)
    entry_altura.insert(0, valores_list[5])
    entry_imagem.delete(0, tk.END)
    entry_imagem.insert(0, valores_list[6])


    # Exibe a imagem do Pokémon (se existir)
    caminho_imagem = valores_list[6]
    if caminho_imagem:
        try:
            img = Image.open(caminho_imagem)
            img = img.resize((150, 150))
            img_tk = ImageTk.PhotoImage(img)
            label_imagem.config(image=img_tk, text="")
            label_imagem.image = img_tk  # mantém referência para evitar GC
        except Exception:
            label_imagem.config(text="Imagem não encontrada", image="")
            label_imagem.image = None
    else:
        label_imagem.config(text="Sem imagem", image="")
        label_imagem.image = None




# ---------------------------------------------------------
# Atualizar Pokémon selecionado com os novos dados (GUI)
# ---------------------------------------------------------
def atualizar_pokemon():
    numero = entry_numero.get().strip()
    nome = entry_nome.get().strip()
    tipo = entry_tipo.get().strip()
    descricao = entry_desc.get("1.0", tk.END).strip()
    peso = parse_float_or_none(entry_peso.get())
    altura = parse_float_or_none(entry_altura.get())
    imagem = entry_imagem.get().strip()


    if not numero:
        messagebox.showerror("Erro", "Selecione um Pokémon para atualizar.")
        return


    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE pokemons
        SET nome=?, tipo=?, descricao=?, peso=?, altura=?, imagem=?
        WHERE numero=?
    """, (nome, tipo, descricao, peso, altura, imagem, int(numero)))
    conexao.commit()
    conexao.close()


    messagebox.showinfo("Sucesso", f"Pokémon Nº {numero} atualizado com sucesso.")
    listar_pokemons()




# ---------------------------------------------------------
# Remover Pokémon selecionado (opcional: botão pode ser usado)
# ---------------------------------------------------------
def excluir_pokemon():
    sel = tree.selection()
    if not sel:
        messagebox.showerror("Erro", "Selecione um Pokémon para excluir.")
        return
    item_id = sel[0]
    valores = tree.item(item_id, "values")
    numero = valores[0]
    if messagebox.askyesno("Confirmar", f"Excluir Pokémon Nº {numero}?"):
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM pokemons WHERE numero = ?", (int(numero),))
        conexao.commit()
        conexao.close()
        listar_pokemons()
        messagebox.showinfo("OK", f"Pokémon Nº {numero} excluído.")




# --------------------------
# Criar interface com Tkinter
# --------------------------
root = tk.Tk()
root.title("Sistema de Pokémons")
root.geometry("900x700")


# Frame de cadastro/edição
frame_form = tk.LabelFrame(root, text="Cadastro / Edição de Pokémon", padx=10, pady=10)
frame_form.pack(fill="x", padx=10, pady=5)


tk.Label(frame_form, text="Número:").grid(row=0, column=0, sticky="w")
entry_numero = tk.Entry(frame_form)
entry_numero.grid(row=0, column=1)


tk.Label(frame_form, text="Nome:").grid(row=1, column=0, sticky="w")
entry_nome = tk.Entry(frame_form)
entry_nome.grid(row=1, column=1)


tk.Label(frame_form, text="Tipo:").grid(row=2, column=0, sticky="w")
entry_tipo = tk.Entry(frame_form)
entry_tipo.grid(row=2, column=1)


tk.Label(frame_form, text="Descrição:").grid(row=3, column=0, sticky="nw")
entry_desc = tk.Text(frame_form, height=3, width=40)
entry_desc.grid(row=3, column=1)


tk.Label(frame_form, text="Peso (kg):").grid(row=4, column=0, sticky="w")
entry_peso = tk.Entry(frame_form)
entry_peso.grid(row=4, column=1)


tk.Label(frame_form, text="Altura (m):").grid(row=5, column=0, sticky="w")
entry_altura = tk.Entry(frame_form)
entry_altura.grid(row=5, column=1)


tk.Label(frame_form, text="Imagem:").grid(row=6, column=0, sticky="w")
entry_imagem = tk.Entry(frame_form, width=40)
entry_imagem.grid(row=6, column=1)
btn_imagem = tk.Button(frame_form, text="Selecionar", command=selecionar_imagem)
btn_imagem.grid(row=6, column=2, padx=5)


# Botões de ação
btn_inserir = tk.Button(frame_form, text="Inserir Pokémon", command=inserir_pokemon)
btn_inserir.grid(row=7, column=0, pady=8)


btn_atualizar = tk.Button(frame_form, text="Atualizar Pokémon", command=atualizar_pokemon)
btn_atualizar.grid(row=7, column=1, pady=8)


btn_excluir = tk.Button(frame_form, text="Excluir Pokémon", command=excluir_pokemon)
btn_excluir.grid(row=7, column=2, pady=8)


# Frame de listagem
frame_lista = tk.LabelFrame(root, text="Pokémons Cadastrados", padx=10, pady=10)
frame_lista.pack(fill="both", expand=True, padx=10, pady=5)


# Colunas que o Treeview irá exibir (usamos exatamente essa ordem em todo lugar)
colunas = ("numero", "nome", "tipo", "descricao", "peso", "altura", "imagem")
tree = ttk.Treeview(frame_lista, columns=colunas, show="headings", height=12)
for col in colunas:
    tree.heading(col, text=col.capitalize())
    tree.column(col, width=120)
tree.pack(side="left", fill="both", expand=True)


scroll = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
tree.configure(yscroll=scroll.set)
scroll.pack(side="right", fill="y")


# Label para exibir imagem do Pokémon selecionado
label_imagem = tk.Label(root, text="Selecione um Pokémon para ver a imagem")
label_imagem.pack(pady=10)


# Evento para mostrar dados + imagem quando clicar em um Pokémon
tree.bind("<<TreeviewSelect>>", mostrar_imagem)


# Inicializa banco, garante coluna imagem e lista pokémons
criar_tabela()
listar_pokemons()


root.mainloop()



