import csv
import os
from datetime import datetime
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle

FILE_NAME = "buku_keuangan_v14.csv"
VIRTUAL_FILE = "daftar_virtual.txt"
KET_MASUK_FILE = "daftar_ket_masuk.txt"
KET_KELUAR_FILE = "daftar_ket_keluar.txt"
ANGGARAN_FILE = "anggaran.txt"

C_BG_GELAP = (0.012, 0.016, 0.369, 1) # #03045E
C_CARD = (0.008, 0.243, 0.541, 1)     # #023E8A
C_BIRU_1 = (0, 0.467, 0.714, 1)       # #0077B6
C_BIRU_2 = (0, 0.588, 0.78, 1)        # #0096C7
C_BIRU_3 = (0, 0.706, 0.847, 1)       # #00B4D8
C_BIRU_4 = (0.282, 0.792, 0.894, 1)   # #48CAE4
C_TEKS_TERANG = (0.792, 0.941, 0.973, 1) # #CAF0F8
C_MASUK = (0.2, 0.8, 0.4, 1)
C_KELUAR = (0.9, 0.3, 0.3, 1)
C_SPIN = C_BIRU_1

Window.clearcolor = C_BG_GELAP

# ==========================================
# WIDGET GAMBAR & TOMBOL KUSTOM
# ==========================================
class NoelMascot(Image):
    def __init__(self, filename='noel1.png', **kwargs):
        super().__init__(**kwargs)
        self.source = filename
        self.allow_stretch = True
        self.keep_ratio = True
        self.size_hint = (None, None)
        self.size = (dp(80), dp(80))

class CardLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*C_CARD)
            self.rect = RoundedRectangle(radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size

class AnimButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (1, 1, 1, 1)
        self.background_normal = ''
    def on_press(self):
        Animation.cancel_all(self, 'opacity')
        self.opacity = 0.55
        Animation(opacity=1, d=0.25).start(self)

# KELAS BARU UNTUK TOMBOL DENGAN IKON DI ATAS & TEKS DI BAWAH
class IconMenuButton(ButtonBehavior, BoxLayout):
    def __init__(self, ikon_file, teks_judul, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), **kwargs)
        with self.canvas.before:
            Color(*C_CARD)
            self.rect = RoundedRectangle(radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.img = Image(source=ikon_file, allow_stretch=True, keep_ratio=True)
        self.lbl = Label(text=teks_judul, font_size='13sp', bold=True, size_hint_y=None, height=dp(25), color=C_TEKS_TERANG, halign='center')
        self.lbl.bind(size=self.lbl.setter('text_size'))
        
        self.add_widget(self.img)
        self.add_widget(self.lbl)
        
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        Animation.cancel_all(self, 'opacity')
        self.opacity = 0.55
        Animation(opacity=1, d=0.25).start(self)

class LeftLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = 'left'
        self.valign = 'middle'
        self.color = C_TEKS_TERANG
        self.bind(size=self.setter('text_size'))

class BaseScreen(Screen):
    def on_pre_enter(self, *args):
        Animation.cancel_all(self, 'opacity')
        self.opacity = 0
        Animation(opacity=1, d=0.3).start(self)

class CountLabel(LeftLabel):
    nilai = NumericProperty(0)
    def on_nilai(self, *args): self.text = rupiah(self.nilai)
    def animasi_ke(self, target):
        Animation.cancel_all(self, 'nilai')
        self.nilai = 0
        Animation(nilai=target, d=0.8, t='out_quad').start(self)

class BarProgress(Widget):
    rasio = NumericProperty(0)
    warna = ListProperty([0.3, 0.8, 0.4, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(1, 1, 1, 0.12)
            self.bg = RoundedRectangle(radius=[dp(6)])
            self.col = Color(*self.warna)
            self.fg = RoundedRectangle(radius=[dp(6)])
        self.bind(pos=self.update, size=self.update, rasio=self.update, warna=self.update)
    def update(self, *args):
        self.bg.pos = self.pos; self.bg.size = self.size
        self.col.rgba = self.warna; self.fg.pos = self.pos
        self.fg.size = (self.width * max(0, min(self.rasio, 1)), self.height)
    def animasi_ke(self, r): Animation(rasio=r, d=0.6, t='out_quad').start(self)

class Keypad(BoxLayout):
    def __init__(self, warna=C_BIRU_3, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(6), size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter('height'))
        self.value = ""
        self.display = Label(text="Rp 0", font_size='30sp', bold=True, size_hint_y=None, height=dp(60), color=warna)
        self.add_widget(self.display)
        quick = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(42))
        for teks, n in (("+10rb", 10000), ("+50rb", 50000), ("+100rb", 100000)):
            b = AnimButton(text=teks, background_color=C_BIRU_2)
            b.bind(on_press=lambda x, n=n: self.tambah(n))
            quick.add_widget(b)
        b_clear = AnimButton(text="Hapus", background_color=C_KELUAR)
        b_clear.bind(on_press=lambda x: self.set_value(""))
        quick.add_widget(b_clear)
        self.add_widget(quick)
        grid = GridLayout(cols=3, spacing=dp(6), size_hint_y=None, height=dp(4 * 52 + 3 * 6))
        for k in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "000", "0", "<"]:
            b = AnimButton(text=k, font_size='20sp', bold=True, background_color=C_CARD)
            b.bind(on_press=lambda x, k=k: self.tekan(k))
            grid.add_widget(b)
        self.add_widget(grid)
    def tekan(self, k):
        if k == "<": self.value = self.value[:-1]
        else:
            nv = (self.value + k).lstrip("0")
            if len(nv) <= 12: self.value = nv
        self.display.text = rupiah(int(self.value or 0))
    def tambah(self, n):
        self.value = str(int(self.value or 0) + n)
        self.display.text = rupiah(int(self.value or 0))
    def set_value(self, v):
        self.value = str(v) if v else ""
        self.display.text = rupiah(int(self.value or 0))
    def angka(self): return int(self.value or 0)

# ==========================================
# FUNGSI BANTU DATA
# ==========================================
def init_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(["Tanggal", "Keterangan", "Dompet", "Tipe", "Nominal"])
    if not os.path.exists(VIRTUAL_FILE):
        with open(VIRTUAL_FILE, 'w', encoding='utf-8') as f: f.write("DANA\nBRI\nShopeePay\n")
    if not os.path.exists(KET_MASUK_FILE):
        with open(KET_MASUK_FILE, 'w', encoding='utf-8') as f: f.write("Gaji\nUang Jajan dari Orang Tua\nBonus\n")
    if not os.path.exists(KET_KELUAR_FILE):
        with open(KET_KELUAR_FILE, 'w', encoding='utf-8') as f: f.write("Makan & Minum\nBensin\nBelanja Kebutuhan\nBayar Utang\nTopup Paylater\n")
    if not os.path.exists(ANGGARAN_FILE):
        with open(ANGGARAN_FILE, 'w', encoding='utf-8') as f: f.write("")

def muat_daftar(nama_file, default_list):
    if not os.path.exists(nama_file): return default_list
    with open(nama_file, 'r', encoding='utf-8') as f: return [line.strip() for line in f if line.strip()]

def rupiah(n): return ("-" if int(n) < 0 else "") + "Rp " + f"{abs(int(n)):,}".replace(",", ".")
def is_transfer(ket): return ket.startswith("Transfer ")

def baca_semua_baris():
    with open(FILE_NAME, 'r', encoding='utf-8') as f: return list(csv.reader(f))
def tulis_semua_baris(baris):
    with open(FILE_NAME, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerows(baris)
def tambah_baris(daftar_baris):
    with open(FILE_NAME, 'a', newline='', encoding='utf-8') as f: csv.writer(f).writerows(daftar_baris)

def baca_transaksi():
    hasil = []
    if not os.path.exists(FILE_NAME): return hasil
    for i, row in enumerate(baca_semua_baris()):
        if i == 0 or len(row) < 5: continue
        try: nom = int(row[4])
        except ValueError: continue
        hasil.append((i, row[0], row[1], row[2], row[3], nom))
    return hasil

def hitung_saldo():
    saldo = {}
    for idx, tgl, ket, dmp, tp, nom in baca_transaksi():
        saldo.setdefault(dmp, 0)
        saldo[dmp] += nom if tp == "Pemasukan" else -nom
    return saldo

def daftar_dompet():
    hasil = ["Cash"]
    for d in muat_daftar(VIRTUAL_FILE, []):
        if d not in hasil: hasil.append(d)
    return hasil

def cari_pasangan(baris, idx):
    row = baris[idx]
    ket = row[1]
    if ket.startswith("Transfer ke "): target = ket[len("Transfer ke "):]; tp_p = "Pemasukan"
    elif ket.startswith("Transfer dari "): target = ket[len("Transfer dari "):]; tp_p = "Pengeluaran"
    else: return None
    for j, r in enumerate(baris):
        if j == idx or j == 0 or len(r) < 5: continue
        if r[0] == row[0] and r[4] == row[4] and r[3] == tp_p and r[2] == target and r[1].startswith("Transfer "): return j
    return None

def hapus_transaksi(idx):
    baris = baca_semua_baris()
    if idx >= len(baris): return
    hapus = {idx}
    p = cari_pasangan(baris, idx)
    if p is not None: hapus.add(p)
    tulis_semua_baris([r for i, r in enumerate(baris) if i not in hapus])

def muat_anggaran():
    hasil = {}
    for line in muat_daftar(ANGGARAN_FILE, []):
        if "|" in line:
            kat, _, val = line.rpartition("|")
            try: hasil[kat] = int(val)
            except ValueError: pass
    return hasil

def simpan_anggaran(data):
    with open(ANGGARAN_FILE, 'w', encoding='utf-8') as f:
        for kat, val in data.items(): f.write(f"{kat}|{val}\n")
# ==========================================
# 1. MENU UTAMA (DASHBOARD)
# ==========================================
class MenuScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        self.noel = NoelMascot('noel1.png')
        header_box.add_widget(self.noel)
        teks_box = BoxLayout(orientation='vertical')
        teks_box.add_widget(LeftLabel(text="Halo, saya nowell asisten keuangan noel", font_size='14sp', color=C_BIRU_4))
        teks_box.add_widget(LeftLabel(text="Keuanganku", font_size='32sp', bold=True, color=C_TEKS_TERANG))
        header_box.add_widget(teks_box)
        layout.add_widget(header_box)

        # Kartu Total Kekayaan dengan Ikon Kekayaan.png
        card_saldo = CardLayout(orientation='vertical', padding=dp(15), spacing=dp(4), size_hint_y=None, height=dp(130))
        box_atas_saldo = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        box_atas_saldo.add_widget(Image(source='Kekayaan.png', size_hint_x=None, width=dp(25), allow_stretch=True, keep_ratio=True))
        box_atas_saldo.add_widget(LeftLabel(text="  sisa wang noel", font_size='16sp', color=C_BIRU_4, bold=True))
        card_saldo.add_widget(box_atas_saldo)
        self.lbl_saldo = CountLabel(font_size='36sp', bold=True, color=C_TEKS_TERANG, size_hint_y=None, height=dp(55))
        card_saldo.add_widget(self.lbl_saldo)
        layout.add_widget(card_saldo)

        # Kartu Ringkasan Masuk/Keluar
        card_ringkasan = CardLayout(orientation='horizontal', padding=dp(15), spacing=dp(10), size_hint_y=None, height=dp(80))
        box_masuk = BoxLayout(orientation='vertical')
        box_masuk.add_widget(LeftLabel(text="Pemasukan Bulan Ini", font_size='12sp', color=C_MASUK))
        self.lbl_masuk = LeftLabel(text="Rp 0", font_size='16sp', bold=True, color=C_TEKS_TERANG)
        box_masuk.add_widget(self.lbl_masuk)
        card_ringkasan.add_widget(box_masuk)
        
        box_keluar = BoxLayout(orientation='vertical')
        box_keluar.add_widget(LeftLabel(text="Pengeluaran Bulan Ini", font_size='12sp', color=C_KELUAR))
        self.lbl_keluar = LeftLabel(text="Rp 0", font_size='16sp', bold=True, color=C_TEKS_TERANG)
        box_keluar.add_widget(self.lbl_keluar)
        card_ringkasan.add_widget(box_keluar)
        layout.add_widget(card_ringkasan)

        # GRID MENU ICON BARU
        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(2 * 120 + 15))
        
        btn_catat = IconMenuButton('Catatransaksi.png', "Catat\nTransaksi")
        btn_catat.bind(on_press=lambda x: setattr(self.manager, 'current', 'tipe'))
        grid.add_widget(btn_catat)
        
        btn_saldo = IconMenuButton('Saldodanmutasi.png', "Saldo &\nMutasi")
        btn_saldo.bind(on_press=lambda x: setattr(self.manager, 'current', 'saldo'))
        grid.add_widget(btn_saldo)
        
        btn_transfer = IconMenuButton('Transfer.png', "Transfer\nDompet")
        btn_transfer.bind(on_press=lambda x: setattr(self.manager, 'current', 'transfer'))
        grid.add_widget(btn_transfer)
        
        btn_anggaran = IconMenuButton('Anggaran.png', "Anggaran\nBulanan")
        btn_anggaran.bind(on_press=lambda x: setattr(self.manager, 'current', 'anggaran'))
        grid.add_widget(btn_anggaran)
        
        layout.add_widget(grid)
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self, *args):
        trans = baca_transaksi(); bulan = datetime.now().strftime("%Y-%m")
        total = 0; masuk = 0; keluar = 0
        for idx, tgl, ket, dmp, tp, nom in trans:
            total += nom if tp == "Pemasukan" else -nom
            if tgl.startswith(bulan) and not is_transfer(ket):
                if tp == "Pemasukan": masuk += nom
                else: keluar += nom
        self.lbl_saldo.animasi_ke(total)
        self.lbl_masuk.text = rupiah(masuk)
        self.lbl_keluar.text = rupiah(keluar)

# ==========================================
# 2. PILIH JENIS TRANSAKSI
# ==========================================
class TipeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        header_box.add_widget(NoelMascot('noel4.png'))
        header_box.add_widget(LeftLabel(text="Uang bang noel + atau - nih?", font_size='20sp', bold=True))
        layout.add_widget(header_box)
        
        # Grid untuk tombol jenis transaksi
        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=0.6)
        
        btn_masuk = IconMenuButton('Masuk.png', "Pemasukan")
        btn_masuk.bind(on_press=lambda x: self.lanjut('Pemasukan'))
        grid.add_widget(btn_masuk)
        
        btn_keluar = IconMenuButton('Keluar.png', "Pengeluaran")
        btn_keluar.bind(on_press=lambda x: self.lanjut('Pengeluaran'))
        grid.add_widget(btn_keluar)
        
        layout.add_widget(grid)
        
        # Tombol Batal Pakai Ikon Kembali
        box_batal = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        img_batal = Image(source='Kembali.png', size_hint_x=None, width=dp(40))
        btn_batal = AnimButton(text="Kembali ke Menu", background_color=C_CARD)
        btn_batal.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        box_batal.add_widget(img_batal)
        box_batal.add_widget(btn_batal)
        layout.add_widget(box_batal)
        
        self.add_widget(layout)

    def lanjut(self, tipe):
        form = self.manager.get_screen('form')
        form.atur_tipe(tipe)
        self.manager.current = 'form'

# ==========================================
# 3. FORM INPUT
# ==========================================
class FormScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tipe_transaksi = ""; self.mode_edit = False; self.edit_idx = -1
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5))
        
        # Header Box dengan Ikon Dinamis (pemasukan.png atau Pengeluaran.png)
        self.header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        self.img_ikon = Image(source='Pemasukan.png', size_hint_x=None, width=dp(50))
        self.header_box.add_widget(self.img_ikon)
        self.title_label = LeftLabel(text="Catat Transaksi", font_size='24sp', bold=True)
        self.header_box.add_widget(self.title_label)
        self.noel = NoelMascot('noel3.png') 
        self.header_box.add_widget(self.noel)
        main_layout.add_widget(self.header_box)
        
        scroll_form = ScrollView(size_hint=(1, 1))
        self.form_card = CardLayout(orientation='vertical', padding=dp(15), spacing=dp(8), size_hint_y=None)
        self.form_card.bind(minimum_height=self.form_card.setter('height'))
        self.form_card.add_widget(LeftLabel(text="Tanggal:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        box_tanggal = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(45))
        self.spin_tahun = Spinner(values=tuple(str(y) for y in range(2023, 2031)), background_color=C_SPIN)
        self.spin_bulan = Spinner(values=tuple(f"{m:02d}" for m in range(1, 13)), background_color=C_SPIN)
        self.spin_hari = Spinner(values=tuple(f"{d:02d}" for d in range(1, 32)), background_color=C_SPIN)
        box_tanggal.add_widget(self.spin_tahun); box_tanggal.add_widget(self.spin_bulan); box_tanggal.add_widget(self.spin_hari)
        self.form_card.add_widget(box_tanggal)
        self.form_card.add_widget(LeftLabel(text="Keterangan:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.ket_spinner = Spinner(text='Pilih', size_hint_y=None, height=dp(45), background_color=C_SPIN)
        self.ket_spinner.bind(text=self.cek_ket)
        self.form_card.add_widget(self.ket_spinner)
        self.input_ket = TextInput(hint_text="Ketik Keterangan Baru", size_hint_y=None, height=0, opacity=0, multiline=False)
        self.form_card.add_widget(self.input_ket)
        self.form_card.add_widget(LeftLabel(text="Disimpan / Sumber:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.jenis_dompet = Spinner(text='Cash', values=('Cash', 'Dana Virtual'), size_hint_y=None, height=dp(45), background_color=C_SPIN)
        self.jenis_dompet.bind(text=self.cek_dompet)
        self.form_card.add_widget(self.jenis_dompet)
        self.virtual_spinner = Spinner(text='Pilih Aplikasi', size_hint_y=None, height=0, opacity=0, background_color=C_BIRU_1)
        self.virtual_spinner.bind(text=self.cek_virtual)
        self.form_card.add_widget(self.virtual_spinner)
        self.input_virtual = TextInput(hint_text="Ketik Nama Aplikasi", size_hint_y=None, height=0, opacity=0, multiline=False)
        self.form_card.add_widget(self.input_virtual)
        self.form_card.add_widget(LeftLabel(text="Nominal:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.keypad = Keypad(warna=C_TEKS_TERANG)
        self.form_card.add_widget(self.keypad)
        scroll_form.add_widget(self.form_card)
        main_layout.add_widget(scroll_form)
        self.status_label = LeftLabel(text="", size_hint_y=None, height=dp(25))
        main_layout.add_widget(self.status_label)
        
        box_tombol = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(55))
        img_batal = Image(source='Kembali.png', size_hint_x=None, width=dp(40))
        btn_kembali = AnimButton(text="Batal", background_color=C_CARD)
        btn_kembali.bind(on_press=self.batal)
        box_tombol.add_widget(img_batal)
        box_tombol.add_widget(btn_kembali)
        self.btn_simpan = AnimButton(text="SIMPAN", background_color=C_BIRU_2, bold=True)
        self.btn_simpan.bind(on_press=self.simpan_data)
        box_tombol.add_widget(self.btn_simpan)
        main_layout.add_widget(box_tombol)
        self.add_widget(main_layout)

    def batal(self, instance):
        self.status_label.text = ""
        if self.mode_edit: self.manager.current = 'saldo'
        else: self.manager.current = 'tipe'

    def atur_tipe(self, tipe):
        self.mode_edit = False; self.tipe_transaksi = tipe
        self.title_label.text = f"Catat {tipe}"
        if tipe == 'Pemasukan': 
            self.noel.source = 'noel3.png'
            self.img_ikon.source = 'pemasukan,png'
        else: 
            self.noel.source = 'noel5.png'
            self.img_ikon.source = 'Pengeluaran.png'
        self.btn_simpan.text = "SIMPAN"; self.status_label.text = ""
        self.siapkan_daftar()
        now = datetime.now()
        self.spin_tahun.text = str(now.year); self.spin_bulan.text = f"{now.month:02d}"; self.spin_hari.text = f"{now.day:02d}"
        self.keypad.set_value(""); self.jenis_dompet.text = 'Cash'

    def muat_untuk_edit(self, idx, tgl, ket, dmp, tp, nom):
        self.mode_edit = True; self.edit_idx = idx; self.tipe_transaksi = tp
        self.title_label.text = f"Edit {tp}"; self.noel.source = 'noel4.png'; self.btn_simpan.text = "UPDATE"
        self.img_ikon.source = 'pemasukan,png' if tp == 'Pemasukan' else 'Pengeluaran.png'
        self.status_label.text = ""; self.siapkan_daftar()
        try:
            thn, bln, hr = tgl.split('-')
            self.spin_tahun.text = thn; self.spin_bulan.text = bln; self.spin_hari.text = hr
        except: pass
        if ket not in self.ket_spinner.values: self.ket_spinner.values = tuple(list(self.ket_spinner.values[:-1]) + [ket, "+ Tambah Keterangan Baru"])
        self.ket_spinner.text = ket
        if dmp == 'Cash': self.jenis_dompet.text = 'Cash'
        else:
            self.jenis_dompet.text = 'Dana Virtual'
            if dmp not in self.virtual_spinner.values: self.virtual_spinner.values = tuple(list(self.virtual_spinner.values[:-1]) + [dmp, "+ Tambah Menu Baru"])
            self.virtual_spinner.text = dmp
        self.keypad.set_value(nom)

    def siapkan_daftar(self):
        file_ket = KET_MASUK_FILE if self.tipe_transaksi == 'Pemasukan' else KET_KELUAR_FILE
        self.daftar_ket = muat_daftar(file_ket, [])
        self.ket_spinner.values = tuple(self.daftar_ket + ["+ Tambah Keterangan Baru"])
        if not self.mode_edit: self.ket_spinner.text = self.daftar_ket[0] if self.daftar_ket else "+ Tambah Keterangan Baru"
        self.daftar_virtual = muat_daftar(VIRTUAL_FILE, ["DANA", "BRI"])
        self.virtual_spinner.values = tuple(self.daftar_virtual + ["+ Tambah Menu Baru"])
        self.cek_dompet(self.jenis_dompet, self.jenis_dompet.text)

    def cek_dompet(self, spinner, text):
        if text == 'Dana Virtual':
            self.virtual_spinner.height = dp(45); self.virtual_spinner.opacity = 1
            if self.virtual_spinner.text not in self.virtual_spinner.values and not self.mode_edit:
                 self.virtual_spinner.text = self.daftar_virtual[0] if self.daftar_virtual else 'Pilih Aplikasi'
            self.cek_virtual(self.virtual_spinner, self.virtual_spinner.text)
        else:
            self.virtual_spinner.height = 0; self.virtual_spinner.opacity = 0
            self.input_virtual.height = 0; self.input_virtual.opacity = 0

    def cek_virtual(self, spinner, text):
        if self.jenis_dompet.text == 'Dana Virtual' and text == "+ Tambah Menu Baru":
            self.input_virtual.height = dp(45); self.input_virtual.opacity = 1
        else:
            self.input_virtual.height = 0; self.input_virtual.opacity = 0; self.input_virtual.text = ""
            
    def cek_ket(self, spinner, text):
        if text == "+ Tambah Keterangan Baru":
            self.input_ket.height = dp(45); self.input_ket.opacity = 1
        else:
            self.input_ket.height = 0; self.input_ket.opacity = 0; self.input_ket.text = ""

    def simpan_data(self, instance):
        tgl = f"{self.spin_tahun.text}-{self.spin_bulan.text}-{self.spin_hari.text}"
        nom = self.keypad.value
        file_ket = KET_MASUK_FILE if self.tipe_transaksi == 'Pemasukan' else KET_KELUAR_FILE
        if self.ket_spinner.text == "+ Tambah Keterangan Baru":
            ket = self.input_ket.text.strip()
            if ket:
                with open(file_ket, 'a', encoding='utf-8') as f: f.write(f"{ket}\n")
        else: ket = self.ket_spinner.text
        if self.jenis_dompet.text == 'Cash': dmp = 'Cash'
        else:
            if self.virtual_spinner.text == "+ Tambah Menu Baru":
                dmp = self.input_virtual.text.strip()
                if dmp:
                    with open(VIRTUAL_FILE, 'a', encoding='utf-8') as f: f.write(f"{dmp}\n")
            else: dmp = self.virtual_spinner.text
        if not ket or ket == "+ Tambah Keterangan Baru" or not dmp or dmp == "+ Tambah Menu Baru" or dmp == "Pilih Aplikasi" or not nom:
            self.status_label.text = "Isi semua data ya, Bos!"; self.status_label.color = C_KELUAR
            return
        baris = baca_semua_baris()
        if self.mode_edit: baris[self.edit_idx] = [tgl, ket, dmp, self.tipe_transaksi, nom]
        else: baris.append([tgl, ket, dmp, self.tipe_transaksi, nom])
        tulis_semua_baris(baris)
        self.status_label.text = "Sip, berhasil disimpan!"; self.status_label.color = C_MASUK
        self.keypad.set_value(""); self.input_ket.text = ""; self.input_virtual.text = ""
        if self.mode_edit: self.manager.current = 'saldo'
        else: self.manager.current = 'menu'
# ==========================================
# 4. SALDO & MUTASI
# ==========================================
class SaldoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._lock = False
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
        
        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        header_box.add_widget(Image(source='Saldodanmutasi.png', size_hint_x=None, width=dp(50)))
        header_box.add_widget(LeftLabel(text="Cek Saldo\n& Mutasi", font_size='22sp', bold=True))
        header_box.add_widget(NoelMascot('noel7.png'))
        layout.add_widget(header_box)

        filter_row = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(42))
        self.spin_bulan = Spinner(text="Semua Bulan", values=("Semua Bulan",), background_color=C_SPIN)
        self.spin_dompet = Spinner(text="Semua Dompet", values=("Semua Dompet",), background_color=C_SPIN)
        self.spin_bulan.bind(text=self.ganti_filter)
        self.spin_dompet.bind(text=self.ganti_filter)
        filter_row.add_widget(self.spin_bulan); filter_row.add_widget(self.spin_dompet)
        layout.add_widget(filter_row)
        
        self.scroll = ScrollView(size_hint=(1, 1))
        self.konten = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(10), spacing=dp(15))
        self.konten.bind(minimum_height=self.konten.setter('height'))
        self.scroll.add_widget(self.konten)
        layout.add_widget(self.scroll)
        
        box_kembali = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55), spacing=dp(10))
        box_kembali.add_widget(Image(source='Kembali.png', size_hint_x=None, width=dp(40)))
        btn_kembali = AnimButton(text="Kembali ke Menu", background_color=C_CARD)
        btn_kembali.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        box_kembali.add_widget(btn_kembali)
        layout.add_widget(box_kembali)
        self.add_widget(layout)

    def hapus_baris(self, idx):
        hapus_transaksi(idx)
        self.tampilkan()
        
    def edit_baris(self, idx, tgl, ket, dmp, tp, nom):
        form = self.manager.get_screen('form')
        form.muat_untuk_edit(idx, tgl, ket, dmp, tp, nom)
        self.manager.current = 'form'

    def ganti_filter(self, *args):
        if not self._lock: self.tampilkan()

    def on_enter(self, *args):
        trans = baca_transaksi(); self._lock = True
        bulan_list = sorted({t[1][:7] for t in trans}, reverse=True)
        self.spin_bulan.values = tuple(["Semua Bulan"] + bulan_list)
        if self.spin_bulan.text not in self.spin_bulan.values: self.spin_bulan.text = "Semua Bulan"
        dompet_list = sorted({t[3] for t in trans})
        self.spin_dompet.values = tuple(["Semua Dompet"] + dompet_list)
        if self.spin_dompet.text not in self.spin_dompet.values: self.spin_dompet.text = "Semua Dompet"
        self._lock = False; self.tampilkan()

    def tampilkan(self):
        self.konten.clear_widgets()
        trans = baca_transaksi()
        if not trans:
            self.konten.add_widget(LeftLabel(text="Belum ada transaksi.", size_hint_y=None, height=dp(30)))
            return

        saldo = {}
        total = 0
        for idx, tgl, ket, dmp, tp, nom in trans:
            saldo.setdefault(dmp, 0)
            if tp == "Pemasukan": saldo[dmp] += nom; total += nom
            else: saldo[dmp] -= nom; total -= nom
        urutan = list(saldo.keys())
        if 'Cash' in urutan: urutan.remove('Cash'); urutan.insert(0, 'Cash')

        summary_card = CardLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        summary_card.bind(minimum_height=summary_card.setter('height'))
        summary_card.add_widget(Label(text="RINGKASAN SALDO", font_size='18sp', bold=True, size_hint_y=None, height=dp(30), color=C_BIRU_4))
        for dmp in urutan:
            s = saldo[dmp]; warna = C_KELUAR if s < 0 else C_TEKS_TERANG
            summary_card.add_widget(LeftLabel(text=f"{dmp}: {rupiah(s)}", font_size='16sp', size_hint_y=None, height=dp(25), color=warna))
        summary_card.add_widget(Label(size_hint_y=None, height=dp(10)))
        summary_card.add_widget(LeftLabel(text=f"TOTAL: {rupiah(total)}", font_size='20sp', bold=True, size_hint_y=None, height=dp(30), color=C_BIRU_3))
        self.konten.add_widget(summary_card)

        f_bulan = self.spin_bulan.text; f_dompet = self.spin_dompet.text
        mutasi = {}
        for t in trans:
            idx, tgl, ket, dmp, tp, nom = t
            if tp not in ("Pemasukan", "Pengeluaran"): continue
            if f_bulan != "Semua Bulan" and not tgl.startswith(f_bulan): continue
            if f_dompet != "Semua Dompet" and dmp != f_dompet: continue
            mutasi.setdefault(dmp, {'Pemasukan': [], 'Pengeluaran': []}); mutasi[dmp][tp].append(t)

        self.konten.add_widget(LeftLabel(text="Riwayat Transaksi:", font_size='16sp', bold=True, size_hint_y=None, height=dp(30), color=C_BIRU_4))
        
        for dmp in urutan:
            if dmp not in mutasi: continue
            card = CardLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
            card.bind(minimum_height=card.setter('height'))
            card.add_widget(Label(text=f"DOMPET {dmp.upper()}", font_size='18sp', bold=True, size_hint_y=None, height=dp(30), color=C_TEKS_TERANG))

            def buat_tabel(judul, warna, data_list, card=card):
                if not data_list: return
                card.add_widget(LeftLabel(text=judul, font_size='14sp', bold=True, size_hint_y=None, height=dp(20), color=warna))
                grid = GridLayout(cols=4, size_hint_y=None, spacing=2)
                grid.bind(minimum_height=grid.setter('height'))
                for teks, lebar in (("Tgl", 0.17), ("Ket", 0.28), ("Nominal", 0.25), ("Aksi", 0.30)):
                    grid.add_widget(Label(text=teks, bold=True, size_hint_y=None, height=dp(30), size_hint_x=lebar, color=C_BIRU_4))

                for idx, tgl, ket, dmp_asli, tp_asli, nom in sorted(data_list, key=lambda t: (t[1], t[0]), reverse=True):
                    grid.add_widget(Label(text=tgl[-5:], size_hint_y=None, height=dp(35), size_hint_x=0.17, font_size='12sp', color=C_TEKS_TERANG))
                    ket_pendek = ket[:10] + ".." if len(ket) > 10 else ket
                    grid.add_widget(Label(text=ket_pendek, size_hint_y=None, height=dp(35), size_hint_x=0.28, font_size='12sp', color=C_TEKS_TERANG))
                    grid.add_widget(Label(text=f"{nom:,}".replace(",", "."), size_hint_y=None, height=dp(35), size_hint_x=0.25, font_size='12sp', color=warna))

                    aksi_box = BoxLayout(orientation='horizontal', spacing=2, size_hint_y=None, height=dp(35), size_hint_x=0.30)
                    btn_edit = AnimButton(text="Edit", font_size='11sp', background_color=C_BIRU_1)
                    btn_edit.bind(on_press=lambda instance, i=idx, t=tgl, k=ket, d=dmp_asli, p=tp_asli, n=nom: self.edit_baris(i, t, k, d, p, n))
                    aksi_box.add_widget(btn_edit)
                    btn_hapus = AnimButton(text="Hapus", font_size='11sp', background_color=C_KELUAR)
                    btn_hapus.bind(on_press=lambda instance, i=idx: self.hapus_baris(i))
                    aksi_box.add_widget(btn_hapus)
                    grid.add_widget(aksi_box)
                card.add_widget(grid)
                card.add_widget(Label(size_hint_y=None, height=dp(10)))
            buat_tabel("PEMASUKAN", C_MASUK, mutasi[dmp]['Pemasukan'])
            buat_tabel("PENGELUARAN", C_KELUAR, mutasi[dmp]['Pengeluaran'])
            self.konten.add_widget(card)

# ==========================================
# 5. TRANSFER & ANGGARAN
# ==========================================
class TransferScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(8))
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        header.add_widget(Image(source='Transfer.png', size_hint_x=None, width=dp(50)))
        header.add_widget(LeftLabel(text="Transfer", font_size='24sp', bold=True))
        header.add_widget(NoelMascot('noel2.png'))
        main.add_widget(header)
        
        scroll = ScrollView(size_hint=(1, 1))
        card = CardLayout(orientation='vertical', padding=dp(15), spacing=dp(8), size_hint_y=None)
        card.bind(minimum_height=card.setter('height'))
        card.add_widget(LeftLabel(text="Dari Dompet:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.spin_dari = Spinner(text="Cash", values=("Cash",), size_hint_y=None, height=dp(45), background_color=C_SPIN)
        card.add_widget(self.spin_dari)
        card.add_widget(LeftLabel(text="Ke Dompet:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.spin_ke = Spinner(text="Cash", values=("Cash",), size_hint_y=None, height=dp(45), background_color=C_SPIN)
        card.add_widget(self.spin_ke)
        card.add_widget(LeftLabel(text="Nominal:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.keypad = Keypad(warna=C_TEKS_TERANG)
        card.add_widget(self.keypad)
        scroll.add_widget(card)
        main.add_widget(scroll)
        
        self.status_label = Label(text="", size_hint_y=None, height=dp(25))
        main.add_widget(self.status_label)
        tombol = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(55))
        
        box_kembali = BoxLayout(orientation='horizontal', size_hint_x=0.4)
        box_kembali.add_widget(Image(source='Kembali.png', size_hint_x=None, width=dp(30)))
        btn_batal = AnimButton(text="Batal", background_color=C_CARD)
        btn_batal.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        box_kembali.add_widget(btn_batal)
        
        btn_ok = AnimButton(text="TRANSFER", bold=True, background_color=C_BIRU_2, size_hint_x=0.6)
        btn_ok.bind(on_press=self.transfer)
        tombol.add_widget(box_kembali)
        tombol.add_widget(btn_ok)
        main.add_widget(tombol)
        self.add_widget(main)

    def on_enter(self, *args):
        dompet = daftar_dompet()
        self.spin_dari.values = tuple(dompet); self.spin_ke.values = tuple(dompet)
        self.spin_dari.text = dompet[0]; self.spin_ke.text = dompet[1] if len(dompet) > 1 else dompet[0]
        self.keypad.set_value(""); self.status_label.text = ""

    def transfer(self, instance):
        dari = self.spin_dari.text; ke = self.spin_ke.text; nom = self.keypad.angka()
        self.status_label.color = C_KELUAR
        if dari == ke: self.status_label.text = "Dompet asal dan tujuan sama!"; return
        if nom <= 0: self.status_label.text = "Isi nominal dulu!"; return
        saldo = hitung_saldo().get(dari, 0)
        if saldo < nom: self.status_label.text = f"Saldo {dari} tidak cukup ({rupiah(saldo)})"; return
        tgl = datetime.now().strftime("%Y-%m-%d")
        tambah_baris([[tgl, f"Transfer ke {ke}", dari, "Pengeluaran", nom], [tgl, f"Transfer dari {dari}", ke, "Pemasukan", nom]])
        self.keypad.set_value(""); self.manager.current = 'menu'

class AnggaranScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=dp(10))
        header.add_widget(Image(source='Anggaran.png', size_hint_x=None, width=dp(50)))
        header.add_widget(LeftLabel(text="Anggaran\nBulanan", font_size='22sp', bold=True))
        header.add_widget(NoelMascot('noel6.png')) 
        main.add_widget(header)

        form = CardLayout(orientation='vertical', padding=dp(12), spacing=dp(6), size_hint_y=None, height=dp(215))
        form.add_widget(LeftLabel(text="Kategori:", size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.spin_kat = Spinner(text="Pilih", values=("Pilih",), size_hint_y=None, height=dp(42), background_color=C_SPIN)
        self.spin_kat.bind(text=self.isi_batas)
        form.add_widget(self.spin_kat)
        form.add_widget(LeftLabel(text="Batas per bulan (Kosongkan utk hapus):", font_size='13sp', size_hint_y=None, height=dp(20), color=C_BIRU_4))
        self.input_batas = TextInput(hint_text="Contoh: 500000", multiline=False, input_filter='int', size_hint_y=None, height=dp(42))
        form.add_widget(self.input_batas)
        btn_simpan = AnimButton(text="SIMPAN ANGGARAN", bold=True, size_hint_y=None, height=dp(45), background_color=C_BIRU_2)
        btn_simpan.bind(on_press=self.simpan)
        form.add_widget(btn_simpan)
        main.add_widget(form)

        self.status_label = Label(text="", size_hint_y=None, height=dp(22))
        main.add_widget(self.status_label)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.konten = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(5))
        self.konten.bind(minimum_height=self.konten.setter('height'))
        self.scroll.add_widget(self.konten)
        main.add_widget(self.scroll)
        
        box_kembali = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55), spacing=dp(10))
        box_kembali.add_widget(Image(source='Kembali.png', size_hint_x=None, width=dp(40)))
        btn_kembali = AnimButton(text="Kembali ke Menu", background_color=C_CARD)
        btn_kembali.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        box_kembali.add_widget(btn_kembali)
        main.add_widget(box_kembali)
        self.add_widget(main)

    def isi_batas(self, spinner, text):
        val = muat_anggaran().get(text)
        self.input_batas.text = str(val) if val else ""

    def on_enter(self, *args):
        kategori = muat_daftar(KET_KELUAR_FILE, [])
        self.spin_kat.values = tuple(kategori) if kategori else ("Pilih",)
        if self.spin_kat.text not in self.spin_kat.values: self.spin_kat.text = kategori[0] if kategori else "Pilih"
        self.isi_batas(self.spin_kat, self.spin_kat.text)
        self.status_label.text = ""; self.tampilkan()

    def simpan(self, instance):
        kat = self.spin_kat.text
        if kat == "Pilih": return
        data = muat_anggaran(); teks = self.input_batas.text.strip()
        if teks and int(teks) > 0:
            data[kat] = int(teks); self.status_label.text = f"Anggaran {kat} disimpan"
        else:
            data.pop(kat, None); self.status_label.text = f"Anggaran {kat} dihapus"
        self.status_label.color = C_MASUK
        simpan_anggaran(data); self.tampilkan()

    def tampilkan(self):
        self.konten.clear_widgets()
        anggaran = muat_anggaran()
        if not anggaran:
            self.konten.add_widget(LeftLabel(text="Belum ada anggaran.", color=C_TEKS_TERANG, size_hint_y=None, height=dp(40)))
            return
        bulan = datetime.now().strftime("%Y-%m"); terpakai = {}
        for idx, tgl, ket, dmp, tp, nom in baca_transaksi():
            if tp == "Pengeluaran" and not is_transfer(ket) and tgl.startswith(bulan):
                terpakai[ket] = terpakai.get(ket, 0) + nom
        for kat, batas in anggaran.items():
            pakai = terpakai.get(kat, 0); rasio = pakai / batas if batas else 0
            if rasio >= 1: warna = list(C_KELUAR)
            elif rasio >= 0.7: warna = [1, 0.8, 0.2, 1] 
            else: warna = list(C_MASUK)
            sisa = batas - pakai
            ket_sisa = f"Sisa {rupiah(sisa)}" if sisa >= 0 else f"Lebih {rupiah(-sisa)}"
            card = CardLayout(orientation='vertical', padding=dp(12), spacing=dp(6), size_hint_y=None, height=dp(100))
            card.add_widget(LeftLabel(text=kat, bold=True, size_hint_y=None, height=dp(24)))
            bar = BarProgress(size_hint_y=None, height=dp(14), warna=warna)
            card.add_widget(bar)
            card.add_widget(LeftLabel(text=f"{rupiah(pakai)} / {rupiah(batas)}  ({int(rasio * 100)}%)  -  {ket_sisa}", font_size='12sp', color=warna, size_hint_y=None, height=dp(24)))
            self.konten.add_widget(card); bar.animasi_ke(rasio)

class KeuanganApp(App):
    def build(self):
        init_file()
        sm = ScreenManager(transition=SlideTransition(duration=0.25))
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(TipeScreen(name='tipe'))
        sm.add_widget(FormScreen(name='form'))
        sm.add_widget(SaldoScreen(name='saldo'))
        sm.add_widget(TransferScreen(name='transfer'))
        sm.add_widget(AnggaranScreen(name='anggaran'))
        return sm

if __name__ == '__main__':
    KeuanganApp().run()
