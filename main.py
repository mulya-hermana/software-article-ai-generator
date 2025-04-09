import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog
import json
import os
import threading
from datetime import datetime

try:
    import requests
except ImportError:
    messagebox.showerror("Module Error", "Modul 'requests' tidak ditemukan. Silakan install dengan perintah: pip install requests")
    raise

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

CONFIG_FILE = "config.json"

class AIWriterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🧠 AI Jago Artikel")
        self.geometry("1200x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.api_provider = tk.StringVar(value="openai")
        self.api_keys = {"openai": "", "deepseek": "", "gemini": ""}
        self.gemini_model = tk.StringVar(value="gemini-2.0-flash")
        self.menu_items = [
            "Dashboard", "Prompt Template", "Keyword Input",
    "Generate Content", "Auto Posting", "Generate Massal",  # Tambahkan ini
    "Settings", "License", "Blog Profile"
]
        self.pages = {}

        self.init_sidebar()
        self.init_main_area()
        self.load_config()
        self.show_page("Dashboard")

    def init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🧠 Jago Artikel AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=(20, 10))

        self.sidebar_buttons = {}
        for item in self.menu_items:
            btn = ctk.CTkButton(self.sidebar, text=item, command=lambda name=item: self.show_page(name))
            btn.pack(pady=5, padx=10, fill="x")
            self.sidebar_buttons[item] = btn

    def init_main_area(self):
        self.main_area = ctk.CTkFrame(self)
        self.main_area.pack(side="right", expand=True, fill="both")

        for item in self.menu_items:
            frame = ctk.CTkFrame(self.main_area)
            self.pages[item] = frame

        # Dashboard
        dashboard = self.pages["Dashboard"]
        ctk.CTkLabel(dashboard, text="Selamat datang di Jago Artikel AI", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        ctk.CTkLabel(dashboard, text="Versi 1.0.0 - Dikembangkan oleh Mulya Hermana").pack(pady=5)

        # Settings Page
        settings = self.pages["Settings"]
        title = ctk.CTkLabel(settings, text="Pengaturan API Key", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)

        settings_form = ctk.CTkFrame(settings)
        settings_form.pack(pady=5)

        ctk.CTkLabel(settings_form, text="Pilih Provider").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.api_provider_dropdown = ctk.CTkComboBox(settings_form, variable=self.api_provider, values=["openai", "deepseek", "gemini"], command=self.update_api_key_input)
        self.api_provider_dropdown.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(settings_form, text="Masukkan API Key").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry = ctk.CTkEntry(settings_form, width=300)
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=5)

        self.gemini_model_label = ctk.CTkLabel(settings_form, text="Model Gemini")
        self.gemini_model_dropdown = ctk.CTkComboBox(settings_form, variable=self.gemini_model, values=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"])

        ctk.CTkButton(settings_form, text="Simpan API Key", command=self.save_api_key).grid(row=3, column=1, pady=10, sticky="e")

        # Prompt Template Page
        prompt = self.pages["Prompt Template"]
        ctk.CTkLabel(prompt, text="Prompt Template", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.prompt_text = ctk.CTkTextbox(prompt, height=300)
        self.prompt_text.pack(padx=20, pady=10, fill="both", expand=True)
        ctk.CTkButton(prompt, text="Simpan Prompt", command=self.save_prompt_template).pack(pady=5)
        self.prompt_file = "prompt_template.txt"
        self.load_prompt_template()

        # Keyword Input Page
        keyword_page = self.pages["Keyword Input"]
        ctk.CTkLabel(keyword_page, text="Masukkan Keyword", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.keyword_entry = ctk.CTkTextbox(keyword_page, height=100, width=600)
        self.keyword_entry.pack(pady=5)
        ctk.CTkLabel(keyword_page, text="Masukkan Judul Artikel").pack()
        self.title_entry = ctk.CTkEntry(keyword_page, width=600)
        self.title_entry.pack(pady=5)
        ctk.CTkButton(keyword_page, text="Buat Judul Otomatis", command=self.generate_title).pack(pady=5)

        # Generate Content Page
        
        generate = self.pages["Generate Content"]
        ctk.CTkLabel(generate, text="Hasil Artikel", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.generated_output = ctk.CTkTextbox(generate)
        self.generated_output.pack(padx=20, pady=10, fill="both", expand=True)
        self.status_label = ctk.CTkLabel(generate, text="", text_color="blue")
        self.status_label.pack()
        button_frame = ctk.CTkFrame(generate)
        button_frame.pack(pady=10)
        self.generate_btn = ctk.CTkButton(button_frame, text="Generate", command=self.generate_article)
        self.generate_btn.pack(side="left", padx=5)
        self.save_txt_btn = ctk.CTkButton(button_frame, text="Simpan ke TXT", command=self.save_to_txt)
        self.save_txt_btn.pack(side="left", padx=5)
        self.save_doc_btn = ctk.CTkButton(button_frame, text="Simpan ke Word", command=self.save_to_word)
        self.save_doc_btn.pack(side="left", padx=5)
        self.post_wp_btn = ctk.CTkButton(button_frame, text="Auto Post ke WordPress", command=self.post_to_wordpress)
        self.post_wp_btn.pack(side="left", padx=5)

        # Auto Posting Page
        auto = self.pages["Auto Posting"]
        ctk.CTkLabel(auto, text="Auto Posting ke WordPress", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.wp_verify_btn = ctk.CTkButton(auto, text="Verifikasi Akun WordPress", command=self.verify_wordpress)
        self.wp_verify_btn.pack(pady=5)
        
        # Generate Massal Page

        # --- Bagian: Generate Massal Page (FULL UPGRADE UI + SCROLLABLE + CRUD) ---

        massal = self.pages["Generate Massal"]

        # Judul halaman
        ctk.CTkLabel(
            massal,
            text="📝 Generate Artikel Massal",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 10))

        # Frame untuk input keyword
        keyword_frame = ctk.CTkFrame(massal)
        keyword_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            keyword_frame,
            text="Masukkan Keyword (1 baris 1 keyword):",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=(5, 2), padx=10)

        self.massal_keyword_input = ctk.CTkTextbox(keyword_frame, height=120)
        self.massal_keyword_input.pack(padx=10, pady=(0, 10), fill="x")

        self.massal_generate_btn = ctk.CTkButton(keyword_frame, text="🚀 Generate Semua Artikel", command=self.generate_massal)
        self.massal_generate_btn.pack(padx=10, pady=5, anchor="e")

        self.massal_status = ctk.CTkLabel(massal, text="", text_color="green")
        self.massal_status.pack(pady=(0, 5))

        # Pembungkus scroll supaya tidak mepet
        scroll_wrapper = ctk.CTkFrame(massal)
        scroll_wrapper.pack(padx=20, pady=10, fill="both", expand=True)

        self.massal_scroll_frame = ctk.CTkScrollableFrame(scroll_wrapper)
        self.massal_scroll_frame.pack(fill="both", expand=True)

        # Tombol aksi bawah
        bottom_btn_frame = ctk.CTkFrame(massal)
        bottom_btn_frame.pack(pady=(10, 20))

        self.save_all_btn = ctk.CTkButton(bottom_btn_frame, text="💾 Simpan Semua Artikel", command=self.save_all_massal)
        self.save_all_btn.pack(side="left", padx=10)

        self.add_blank_btn = ctk.CTkButton(bottom_btn_frame, text="➕ Tambah Artikel Kosong", command=self.add_blank_massal)
        self.add_blank_btn.pack(side="left", padx=10)

        self.massal_editors = []

        
        # Tambahkan di bawah self.wp_verify_btn
        ctk.CTkLabel(auto, text="Status Artikel").pack()
        self.wp_status_option = ctk.CTkComboBox(auto, values=["publish", "draft", "pending"])
        self.wp_status_option.pack(pady=5)
        self.wp_status_option.set("publish")

        ctk.CTkLabel(auto, text="Kategori (ID, pisahkan koma)").pack()
        self.wp_category_entry = ctk.CTkEntry(auto, width=400)
        self.wp_category_entry.pack(pady=5)

        ctk.CTkLabel(auto, text="Tags (pisahkan koma)").pack()
        self.wp_tags_entry = ctk.CTkEntry(auto, width=400)
        self.wp_tags_entry.pack(pady=5)

        # Blog Profile Page
        blog = self.pages["Blog Profile"]
        ctk.CTkLabel(blog, text="Blog Profile", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        blog_form = ctk.CTkFrame(blog)
        blog_form.pack(pady=10)

        labels = ["Nama Blog", "URL", "Username", "Password"]
        entries = []
        for i, label in enumerate(labels):
            ctk.CTkLabel(blog_form, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            entry = ctk.CTkEntry(blog_form, width=400, show="*" if label == "Password" else "")
            entry.grid(row=i, column=1, pady=5, sticky="w")
            entries.append(entry)

        self.blog_name_entry, self.blog_url_entry, self.blog_user_entry, self.blog_pass_entry = entries
        ctk.CTkButton(blog_form, text="Simpan Profil Blog", command=self.save_blog_profile).grid(row=4, column=1, sticky="e", pady=10)

    def update_api_key_input(self, *args):
        provider = self.api_provider.get()
        self.api_key_entry.delete(0, tk.END)
        self.api_key_entry.insert(0, self.api_keys.get(provider, ""))

        if provider == "gemini":
            self.gemini_model_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.gemini_model_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        else:
            self.gemini_model_label.grid_forget()
            self.gemini_model_dropdown.grid_forget()

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        if name == "Settings":
            self.update_api_key_input()

    def save_api_key(self):
        provider = self.api_provider.get()
        self.api_keys[provider] = self.api_key_entry.get().strip()
        self.save_config()
        messagebox.showinfo("Sukses", f"API Key untuk {provider} disimpan.")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.api_keys.update(data.get("api_keys", {}))

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_keys": self.api_keys}, f)

    def save_blog_profile(self):
        blog_info = {
            "name": self.blog_name_entry.get().strip(),
            "url": self.blog_url_entry.get().strip(),
            "username": self.blog_user_entry.get().strip(),
            "password": self.blog_pass_entry.get().strip()
        }
        with open("blog_config.json", "w") as f:
            json.dump(blog_info, f)
        messagebox.showinfo("Sukses", "Profil blog berhasil disimpan.")

    def save_prompt_template(self):
        with open(self.prompt_file, "w", encoding="utf-8") as f:
            f.write(self.prompt_text.get("1.0", tk.END).strip())
        messagebox.showinfo("Sukses", "Prompt template berhasil disimpan.")

    def load_prompt_template(self):
        if os.path.exists(self.prompt_file):
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.prompt_text.insert("1.0", content)

    def generate_title(self):
        keywords = self.keyword_entry.get("1.0", tk.END).strip()
        if not keywords:
            messagebox.showwarning("Keyword kosong", "Silakan isi keyword terlebih dahulu.")
            return

        # Prompt untuk AI
        prompt = f"Buatkan satu judul artikel yang menarik dan SEO-friendly dari keyword berikut:\n\n{keywords}, saat generate kamu langsung cantumkan juudulnya tanpa di awali kalimat dan hilangkan tanda *"

        provider = self.api_provider.get()
        api_key = self.api_keys.get(provider, "")

        def worker():
            try:
                if provider == "deepseek":
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    data = {
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                    response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
                    result = response.json()["choices"][0]["message"]["content"]

                elif provider == "openai":
                    openai.api_key = api_key
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    result = response["choices"][0]["message"]["content"]

                elif provider == "gemini":
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(self.gemini_model.get())
                    response = model.generate_content(prompt)
                    result = response.text

                else:
                    raise Exception("Provider tidak dikenali.")

                # Masukkan hasil judul ke field
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, result.strip())

            except Exception as e:
                messagebox.showerror("Gagal", f"Gagal membuat judul otomatis: {str(e)}")

        threading.Thread(target=worker).start()

    def add_blank_massal(self):
        keyword = simpledialog.askstring("Tambah Artikel Kosong", "Masukkan judul/keyword artikel:")
        if keyword:
            self.create_massal_editor(keyword, "")
   
    def create_massal_editor(self, keyword, content):
        article_frame = ctk.CTkFrame(self.massal_scroll_frame)
        article_frame.pack(fill="x", pady=10)

        label = ctk.CTkLabel(article_frame, text=f"Keyword: {keyword}", anchor="w")
        label.pack(anchor="w", padx=5)

        textbox = ctk.CTkTextbox(article_frame, height=200)
        textbox.insert("1.0", content)
        textbox.pack(fill="x", padx=5, pady=5)

        btn_frame = ctk.CTkFrame(article_frame)
        btn_frame.pack(padx=5, pady=(0, 5), anchor="w")

        ctk.CTkButton(btn_frame, text="🗑 Hapus", command=lambda: self.delete_massal(article_frame, keyword)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="📄 Export", command=lambda: self.export_massal(keyword, textbox)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🌐 Post", command=lambda: self.post_massal(keyword, textbox)).pack(side="left", padx=2)

        self.massal_editors.append((keyword, textbox))

    def generate_article(self):
        prompt_template = self.prompt_text.get("1.0", tk.END).strip()
        keyword = self.keyword_entry.get("1.0", tk.END).strip()
        title = self.title_entry.get().strip()

        if not prompt_template or not keyword:
            messagebox.showwarning("Data kurang", "Pastikan prompt dan keyword sudah diisi.")
            return

        final_prompt = prompt_template.replace("{keyword}", keyword).replace("{title}", title)
        self.status_label.configure(text="⏳ Sedang membuat artikel...", text_color="blue")
        self.update_idletasks()

        provider = self.api_provider.get()
        api_key = self.api_keys.get(provider, "")

        def worker():
            try:
                if provider == "deepseek":
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    data = {
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": final_prompt}],
                        "temperature": 0.7
                    }
                    response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
                    result = response.json()["choices"][0]["message"]["content"]
                elif provider == "openai":
                    openai.api_key = api_key
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": final_prompt}],
                        temperature=0.7
                    )
                    result = response["choices"][0]["message"]["content"]
                elif provider == "gemini":
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(self.gemini_model.get())
                    response = model.generate_content(final_prompt)
                    result = response.text
                else:
                    raise Exception("Provider tidak dikenali.")

                self.generated_output.delete("1.0", tk.END)
                self.generated_output.insert(tk.END, result)
                self.status_label.configure(text="✅ Artikel berhasil dibuat.", text_color="green")
            except Exception as e:
                self.status_label.configure(text=f"❌ Gagal: {str(e)}", text_color="red")

        threading.Thread(target=worker).start()
    def generate_massal(self):
        keywords = self.massal_keyword_input.get("1.0", tk.END).strip().splitlines()
        prompt_template = self.prompt_text.get("1.0", tk.END).strip()
        if not keywords or not prompt_template:
            messagebox.showwarning("Data kosong", "Isi keyword dan prompt template terlebih dahulu.")
            return

        self.massal_status.configure(text="⏳ Menghasilkan artikel...", text_color="blue")
        self.massal_scroll_frame.destroy()
        self.massal_scroll_frame = ctk.CTkScrollableFrame(self.pages["Generate Massal"], width=1000, height=00)
        self.massal_scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.massal_editors.clear()

        provider = self.api_provider.get()
        api_key = self.api_keys.get(provider, "")

    

        def worker():
            for i, keyword in enumerate(keywords, 1):
                title = f"Artikel tentang {keyword}"
                prompt = prompt_template.replace("{keyword}", keyword).replace("{title}", title)

                try:
                    if provider == "deepseek":
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}"
                        }
                        data = {
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7
                        }
                        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
                        result = response.json()["choices"][0]["message"]["content"]

                    elif provider == "openai":
                        openai.api_key = api_key
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7
                        )
                        result = response["choices"][0]["message"]["content"]

                    elif provider == "gemini":
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(self.gemini_model.get())
                        response = model.generate_content(prompt)
                        result = response.text

                    else:
                        raise Exception("Provider tidak dikenali.")

                    label = ctk.CTkLabel(self.massal_scroll_frame, text=f"Keyword: {keyword}", anchor="w")
                    label.pack(padx=5, pady=2, anchor="w")

                    textbox = ctk.CTkTextbox(self.massal_scroll_frame, height=200)
                    textbox.insert("1.0", result.strip())
                    textbox.pack(padx=5, pady=5, fill="x", expand=True)

                    self.massal_editors.append((keyword, textbox))
                    self.massal_status.configure(text=f"✅ Artikel {i}/{len(keywords)} selesai", text_color="green")
                    self.update_idletasks()

                except Exception as e:
                    self.massal_status.configure(text=f"❌ Gagal: {keyword} — {str(e)}", text_color="red")

            self.massal_status.configure(text="✅ Semua artikel selesai digenerate.", text_color="green")

        threading.Thread(target=worker).start()

    
    def save_all_massal(self):
        if not self.massal_editors:
            messagebox.showinfo("Kosong", "Tidak ada artikel yang bisa disimpan.")
            return

        for i, (keyword, textbox) in enumerate(self.massal_editors, 1):
            content = textbox.get("1.0", tk.END).strip()
            filename = f"artikel_massal_{i}_{keyword[:30].replace(' ', '_')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

        messagebox.showinfo("Selesai", "Semua artikel berhasil disimpan ke file.")


    def save_to_txt(self):
        content = self.generated_output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Kosong", "Tidak ada artikel yang bisa disimpan.")
            return
        with open(f"artikel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Disimpan", "Artikel berhasil disimpan sebagai TXT.")

    def save_to_word(self):
        try:
            from docx import Document
        except ImportError:
            messagebox.showerror("Error", "Modul 'python-docx' belum terinstal. Gunakan: pip install python-docx")
            return

        content = self.generated_output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Kosong", "Tidak ada artikel yang bisa disimpan.")
            return

        doc = Document()
        doc.add_paragraph(content)
        doc.save(f"artikel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
        messagebox.showinfo("Disimpan", "Artikel berhasil disimpan sebagai Word.")

   
 
    def post_to_wordpress(self):  # ← Harus di dalam class
        content = self.generated_output.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Kosong", "Tidak ada artikel untuk diposting.")
            return

        if not os.path.exists("blog_config.json"):
            messagebox.showerror("Error", "Profil blog belum disimpan.")
            return

        with open("blog_config.json", "r") as f:
            cfg = json.load(f)

        try:
            base_url = cfg['url'].rstrip('/')
            auth = (cfg['username'], cfg['password'])
            headers = {'Content-Type': 'application/json'}

            title = self.title_entry.get()
            status = self.wp_status_option.get()
            category_ids = [
                int(x.strip()) for x in self.wp_category_entry.get().split(',')
                if x.strip().isdigit()
            ]
            tag_names = [
                tag.strip() for tag in self.wp_tags_entry.get().split(',')
                if tag.strip()
            ]
            tag_ids = []

            for tag in tag_names:
                tag_search = requests.get(
                    f"{base_url}/wp-json/wp/v2/tags",
                    params={"search": tag},
                    auth=auth
                )
                tag_result = tag_search.json()
                if isinstance(tag_result, list) and len(tag_result) > 0:
                    tag_ids.append(tag_result[0]["id"])
                else:
                    create_tag = requests.post(
                        f"{base_url}/wp-json/wp/v2/tags",
                        headers=headers,
                        auth=auth,
                        data=json.dumps({"name": tag})
                    )
                    if create_tag.status_code == 201:
                        tag_ids.append(create_tag.json()["id"])

            post_data = {
                "title": title,
                "content": content,
                "status": status,
                "categories": category_ids,
                "tags": tag_ids
            }

            post_url = f"{base_url}/wp-json/wp/v2/posts"
            response = requests.post(
                post_url,
                headers=headers,
                auth=auth,
                data=json.dumps(post_data)
            )

            if response.status_code == 201:
                messagebox.showinfo("Sukses", "Artikel berhasil diposting ke WordPress.")
            else:
                messagebox.showerror("Gagal", f"Gagal posting: {response.text}")
        except Exception as e:
            messagebox.showerror("Gagal", str(e))



    def verify_wordpress(self):
        self.post_to_wordpress()

if __name__ == "__main__":
    app = AIWriterApp()
    app.mainloop()
