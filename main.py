#!/usr/bin/env python3

import sys
import os
import signal
import getpass
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTreeView, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QHeaderView,
                             QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, QItemSelectionModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor

# Módulos locales
from widgets import GraphWidget
from logic import get_system_stats, get_processes_info

class CuerdWatch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CuerdWatch")
        self.resize(1100, 750)
        self.current_user = getpass.getuser()
        self.view_mode = "all"
        
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 5) # Margen inferior reducido
        
        # Cabecera
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>CuerdWatch</b>"))
        header.addStretch()
        self.info_btn = QPushButton("ⓘ")
        self.info_btn.setFixedSize(30, 30)
        self.info_btn.setStyleSheet("background: transparent; color: #aaa; border: none; font-size: 16px;")
        self.info_btn.clicked.connect(self.show_about_dialog)
        header.addWidget(self.info_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QTabWidget::pane { border: 1px solid #333; }
            QTreeView { background-color: #1e1e1e; color: #ddd; selection-background-color: #2e7d32; border: none; }
            QHeaderView::section { background-color: #252525; color: white; padding: 5px; border: 1px solid #111; }
            QPushButton#actionBtn { background-color: #2e7d32; color: white; border-radius: 3px; padding: 5px 12px; }
            QLineEdit { background-color: #252525; color: white; border: 1px solid #444; padding: 4px; border-radius: 3px; }
            QLabel { color: #eee; }
        """)

        self.setup_processes_tab()
        self.setup_performance_tab()

    def setup_processes_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        
        top = QHBoxLayout()
        for mode, label in [("all", "Todos"), ("my", "Mis Procesos"), ("non-root", "No-Root")]:
            btn = QPushButton(label); btn.setObjectName("actionBtn")
            btn.clicked.connect(lambda ch, m=mode: self.set_view_mode(m))
            top.addWidget(btn)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar proceso...")
        top.addWidget(self.search_bar)
        lay.addLayout(top)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["PID", "Nombre", "CPU %", "Mem %", "Usuario", "Estado"])
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        lay.addWidget(self.tree)
        
        bottom = QHBoxLayout()
        self.status_lbl = QLabel("Iniciando...")
        bottom.addWidget(self.status_lbl)
        bottom.addStretch()
        
        btn_kill = QPushButton("MATAR PROCESO")
        btn_kill.setFixedWidth(140)
        btn_kill.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 6px;")
        btn_kill.clicked.connect(self.kill_selected)
        bottom.addWidget(btn_kill)
        lay.addLayout(bottom)
        
        self.tabs.addTab(tab, "Procesos")

    def setup_performance_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        from PySide6.QtWidgets import QGridLayout
        
        grid = QGridLayout()
        self.cpu_graph = GraphWidget("CPU", QColor(46, 204, 113))
        self.cpu_info = QLabel("-")
        self.mem_graph = GraphWidget("RAM", QColor(230, 126, 34))
        self.mem_info = QLabel("-")
        self.disk_graph = GraphWidget("Disco", QColor(52, 152, 219))
        self.disk_info = QLabel("-")
        
        grid.addWidget(QLabel("<b>CPU</b>"), 0, 0)
        grid.addWidget(self.cpu_graph, 1, 0)
        grid.addWidget(self.cpu_info, 1, 1, Qt.AlignTop)
        
        grid.addWidget(QLabel("<b>Memoria</b>"), 2, 0)
        grid.addWidget(self.mem_graph, 3, 0)
        grid.addWidget(self.mem_info, 3, 1, Qt.AlignTop)
        
        grid.addWidget(QLabel("<b>Disco Principal</b>"), 4, 0)
        grid.addWidget(self.disk_graph, 5, 0)
        grid.addWidget(self.disk_info, 5, 1, Qt.AlignTop)

        lay.addLayout(grid)
        
        # EL ARREGLO DEL ESPACIO: Empuja todo hacia arriba
        lay.addStretch(1) 
        
        self.sys_details = QLabel("Sistema")
        self.sys_details.setStyleSheet("color: #777; font-size: 11px; border-top: 1px solid #2a2a2a; padding-top: 4px;")
        lay.addWidget(self.sys_details)
        
        self.tabs.addTab(tab, "Rendimiento")

    def refresh_data(self):
        # 1. Guardar selección por PID
        selected_pid = None
        current_idx = self.tree.currentIndex()
        if current_idx.isValid():
            pid_item = self.model.item(current_idx.row(), 0)
            if pid_item: selected_pid = pid_item.text()

        # 2. Obtener datos
        stats = get_system_stats()
        procs = get_processes_info(self.view_mode, self.current_user, self.search_bar.text())

        # 3. Actualizar Gráficas
        self.cpu_graph.update_data(stats['cpu_perc'])
        self.cpu_info.setText(f"Utilización: {stats['cpu_perc']}%\nVelocidad: {stats['cpu_freq']/1000:.2f} GHz\nNúcleos: {stats['cores']}")
        self.mem_graph.update_data(stats['mem_perc'])
        self.mem_info.setText(f"En uso: {stats['mem_used']:.1f} GB\nTotal: {stats['mem_total']:.1f} GB\n({stats['mem_perc']}%)")
        self.disk_graph.update_data(stats['disk_perc'])
        self.disk_info.setText(f"Uso: {stats['disk_used']:.1f} GB\nTotal: {stats['disk_total']:.1f} GB")
        self.sys_details.setText(f"OS: {stats['os']} | Uptime: {stats['uptime']}")

        # 4. Actualizar Tabla
        self.model.removeRows(0, self.model.rowCount())
        restore_idx = None
        
        for p in procs:
            pid_str = str(p['pid'])
            row = [QStandardItem(pid_str), QStandardItem(p['name']), 
                   QStandardItem(f"{p['cpu_percent']:.1f}"), QStandardItem(f"{p['memory_percent']:.1f}"),
                   QStandardItem(p['username']), QStandardItem(p['status'])]
            self.model.appendRow(row)
            
            if pid_str == selected_pid:
                restore_idx = self.model.index(self.model.rowCount() - 1, 0)

        # 5. Restaurar Selección de forma forzada
        if restore_idx:
            self.tree.setCurrentIndex(restore_idx)
            self.tree.selectionModel().select(restore_idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)

        self.status_lbl.setText(f"Procesos: {len(procs)} | Vista: {self.view_mode}")

    def show_about_dialog(self):
        about = QMessageBox(self)
        about.setWindowTitle("Acerca de CuerdWatch")
        title = "CuerdWatch 1.0"
        description = "Monitor de procesos y rendimiento del sistema"
        copyright_info = "© CuerdOS 2026"
        website = "https://cuerdos.github.io"
        about.setText(f"<b>{title}</b>")
        about.setInformativeText(f"{description}\n\n{copyright_info}\n\nSitio web: {website}")
        
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            about.setIconPixmap(QPixmap(logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            about.setIcon(QMessageBox.Information)
        about.exec()

    def set_view_mode(self, mode):
        self.view_mode = mode
        self.refresh_data()

    def kill_selected(self):
        idx = self.tree.currentIndex()
        if not idx.isValid(): return
        pid = int(self.model.item(idx.row(), 0).text())
        reply = QMessageBox.question(self, "Confirmar", f"¿Matar PID {pid}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try: os.kill(pid, signal.SIGKILL); self.refresh_data()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CuerdWatch(); window.show()
    sys.exit(app.exec())