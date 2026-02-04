import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import csv
import re
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

# Modern color scheme - Light theme
COLORS = {
    'bg_dark': '#f5f5f5',
    'bg_medium': '#ffffff',
    'bg_light': '#e8e8e8',
    'accent': '#2196F3',
    'accent_hover': '#1976D2',
    'text': '#333333',
    'text_muted': '#666666',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'border': '#d0d0d0'
}

class ModernButton(tk.Canvas):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command=None, width=120, height=32, 
                 bg=COLORS['accent'], hover_bg=COLORS['accent_hover'], fg=COLORS['text']):
        super().__init__(parent, width=width, height=height, 
                        bg=parent.cget('bg'), highlightthickness=0)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.text = text
        self.width = width
        self.height = height
        
        self._draw_button(self.bg)
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
    
    def _draw_button(self, color):
        self.delete('all')
        # Rounded rectangle
        radius = 6
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, 0, self.width, radius*2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, self.height-radius*2, radius*2, self.height, start=180, extent=90, fill=color, outline=color)
        self.create_arc(self.width-radius*2, self.height-radius*2, self.width, self.height, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(radius, 0, self.width-radius, self.height, fill=color, outline=color)
        self.create_rectangle(0, radius, self.width, self.height-radius, fill=color, outline=color)
        # Text
        self.create_text(self.width//2, self.height//2, text=self.text, fill=self.fg, font=('Segoe UI', 10, 'bold'))
    
    def _on_enter(self, event):
        self._draw_button(self.hover_bg)
    
    def _on_leave(self, event):
        self._draw_button(self.bg)
    
    def _on_click(self, event):
        if self.command:
            self.command()


class CsvPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title('📊 CSV Plotter Pro')
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.geometry('1200x800')
        self.df = None

        # Configure ttk styles
        self._setup_styles()

        # Main container
        main_container = tk.Frame(root, bg=COLORS['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header frame
        header = tk.Frame(main_container, bg=COLORS['bg_medium'], height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header, text='📊 CSV Plotter Pro', 
                              font=('Segoe UI', 18, 'bold'), 
                              fg=COLORS['text'], bg=COLORS['bg_medium'])
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Controls panel (left side) - with scrollable content
        left_panel = tk.Frame(main_container, bg=COLORS['bg_medium'], width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # File section
        self._create_section(left_panel, '📁 Fichier', 0)
        
        file_frame = tk.Frame(left_panel, bg=COLORS['bg_medium'])
        file_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        self.load_btn = ModernButton(file_frame, '📂 Charger CSV', self.load_csv, width=250, height=28)
        self.load_btn.pack(pady=3)
        
        self.file_label = tk.Label(file_frame, text='Aucun fichier chargé', 
                                   font=('Segoe UI', 8), fg=COLORS['text_muted'], 
                                   bg=COLORS['bg_medium'], wraplength=240)
        self.file_label.pack(pady=2)
        
        # Compare button (initially hidden)
        self.compare_btn = ModernButton(file_frame, '🔄 Comparer avec...', self.load_compare_csv, 
                                        width=250, height=28, bg=COLORS['warning'], hover_bg='#F57C00')
        # Don't pack yet - will be shown after first file is loaded
        
        self.compare_label = tk.Label(file_frame, text='', 
                                      font=('Segoe UI', 8), fg=COLORS['text_muted'], 
                                      bg=COLORS['bg_medium'], wraplength=240)
        # Don't pack yet
        
        # Cancel compare button (initially hidden)
        self.cancel_compare_btn = ModernButton(file_frame, '❌ Annuler comparaison', self.cancel_compare, 
                                               width=250, height=28, bg='#f44336', hover_bg='#d32f2f')
        # Don't pack yet

        # Axes section
        self._create_section(left_panel, '📈 Axes', 1)
        
        axes_frame = tk.Frame(left_panel, bg=COLORS['bg_medium'])
        axes_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        # X axis
        tk.Label(axes_frame, text='Axe X', font=('Segoe UI', 9, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_medium']).pack(anchor='w')
        self.x_var = tk.StringVar(value='Index')
        self.x_combo = ttk.Combobox(axes_frame, textvariable=self.x_var, 
                                    values=['Index'], state='readonly', width=35)
        self.x_combo.pack(fill=tk.X, pady=(1, 5))
        
        # Y axis
        tk.Label(axes_frame, text='Axe Y', font=('Segoe UI', 9, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_medium']).pack(anchor='w')
        self.y_var = tk.StringVar(value='')
        self.y_combo = ttk.Combobox(axes_frame, textvariable=self.y_var, 
                                    values=[], state='readonly', width=35)
        self.y_combo.pack(fill=tk.X, pady=(1, 5))

        # Filter section
        self.filter_section = self._create_section(left_panel, '🎚️ Filtre Butterworth', 2)
        
        self.filter_frame = tk.Frame(left_panel, bg=COLORS['bg_medium'])
        self.filter_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        filter_frame = self.filter_frame
        
        # Sampling frequency display (more compact)
        freq_display = tk.Frame(filter_frame, bg=COLORS['bg_light'], padx=8, pady=5)
        freq_display.pack(fill=tk.X, pady=(0, 5))
        
        freq_row = tk.Frame(freq_display, bg=COLORS['bg_light'])
        freq_row.pack(fill=tk.X)
        tk.Label(freq_row, text='Fréq. échant.:', font=('Segoe UI', 9),
                fg=COLORS['text_muted'], bg=COLORS['bg_light']).pack(side=tk.LEFT)
        self.sampling_freq_label = tk.Label(freq_row, text='— Hz', 
                                            font=('Segoe UI', 12, 'bold'),
                                            fg=COLORS['success'], bg=COLORS['bg_light'])
        self.sampling_freq_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Cutoff frequency input
        tk.Label(filter_frame, text='Fréquence de coupure (Hz)', font=('Segoe UI', 9),
                fg=COLORS['text'], bg=COLORS['bg_medium']).pack(anchor='w', pady=(3, 1))
        
        self.filter_freq_var = tk.StringVar(value='1.0')
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_freq_var, 
                                      width=38, font=('Segoe UI', 10))
        self.filter_entry.pack(fill=tk.X, pady=(0, 5))
        
        self.filter_btn = ModernButton(filter_frame, '🔊 Appliquer filtre', 
                                       self.apply_filter, width=250, height=28,
                                       bg=COLORS['success'], hover_bg='#388E3C')
        self.filter_btn.pack(pady=3)

        # Export section
        self.export_section = self._create_section(left_panel, '💾 Export', 3)
        
        self.export_frame = tk.Frame(left_panel, bg=COLORS['bg_medium'])
        self.export_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        export_frame = self.export_frame
        
        self.export_filtered_var = tk.BooleanVar(value=False)
        self.export_check = ttk.Checkbutton(export_frame, text='Exporter données filtrées',
                                            variable=self.export_filtered_var)
        self.export_check.pack(anchor='w', pady=(0, 5))
        
        self.export_btn = ModernButton(export_frame, '💾 Exporter CSV', 
                                       self.export_csv, width=250, height=28,
                                       bg=COLORS['accent'], hover_bg=COLORS['accent_hover'])
        self.export_btn.pack(pady=3)

        # Graph area (right side)
        graph_container = tk.Frame(main_container, bg=COLORS['bg_medium'])
        graph_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Matplotlib figure with light theme
        self.fig = Figure(figsize=(8, 5), facecolor=COLORS['bg_medium'])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar with min/max info
        status_frame = tk.Frame(graph_container, bg=COLORS['bg_light'], height=50)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        status_frame.pack_propagate(False)
        
        # Left side: general info
        self.index_label = tk.Label(status_frame, text='💡 Chargez un fichier CSV pour commencer', 
                                    font=('Segoe UI', 9), fg=COLORS['text_muted'], 
                                    bg=COLORS['bg_light'])
        self.index_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Right side: min/max values
        minmax_frame = tk.Frame(status_frame, bg=COLORS['bg_light'])
        minmax_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.minmax_label = tk.Label(minmax_frame, text='', 
                                     font=('Segoe UI', 9), fg=COLORS['text'], 
                                     bg=COLORS['bg_light'])
        self.minmax_label.pack(side=tk.RIGHT)

        # Track plot state for index selection
        self.x_data = None
        self.y_data = None
        self.y_filtered = None
        self.x_is_index = False
        self.selected_indices = []
        self.y_choice = None
        self.sampling_frequency = 1000
        self.loaded_file_path = None
        self._suspend_auto_plot = False
        
        # Comparison mode
        self.compare_mode = False
        self.df_compare = None
        self.compare_file_path = None
        self.x_data_compare = None
        self.y_data_compare = None

        # Mouse/zoom state
        self._zoom_rect = None
        self._press_event = None
        self._is_dragging = False
        self._base_xlim = None
        self._base_ylim = None

        # Connect mouse events
        self.fig.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.fig.canvas.mpl_connect('button_release_event', self._on_mouse_release)

        # Bind combobox events
        self.x_combo.bind('<<ComboboxSelected>>', lambda e: self._on_axis_change())
        self.y_combo.bind('<<ComboboxSelected>>', lambda e: self._on_axis_change())

    def _setup_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Combobox style
        style.configure('TCombobox', 
                       fieldbackground=COLORS['bg_light'],
                       background=COLORS['bg_light'],
                       foreground=COLORS['text'],
                       arrowcolor=COLORS['text'],
                       padding=8)
        style.map('TCombobox', 
                 fieldbackground=[('readonly', COLORS['bg_light'])],
                 selectbackground=[('readonly', COLORS['accent'])],
                 selectforeground=[('readonly', COLORS['text'])])
        
        # Entry style
        style.configure('TEntry',
                       fieldbackground=COLORS['bg_light'],
                       foreground=COLORS['text'],
                       padding=8)
        
        # Checkbutton style
        style.configure('TCheckbutton',
                       background=COLORS['bg_medium'],
                       foreground=COLORS['text'],
                       font=('Segoe UI', 10))

    def _create_section(self, parent, title, row):
        """Create a section header"""
        frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        frame.pack(fill=tk.X, padx=15, pady=(10, 3))
        
        tk.Label(frame, text=title, font=('Segoe UI', 10, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_medium']).pack(anchor='w')
        
        # Separator line
        separator = tk.Frame(frame, bg=COLORS['accent'], height=2)
        separator.pack(fill=tk.X, pady=(3, 0))
        
        return frame

    def _style_axes(self):
        """Apply light theme to matplotlib axes"""
        self.ax.set_facecolor('#ffffff')
        self.ax.tick_params(colors=COLORS['text'], which='both')
        self.ax.xaxis.label.set_color(COLORS['text'])
        self.ax.yaxis.label.set_color(COLORS['text'])
        self.ax.title.set_color(COLORS['text'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        self.ax.grid(True, color=COLORS['border'], alpha=0.5, linestyle='--')

    def _on_axis_change(self):
        """Handle axis selection change"""
        if not self._suspend_auto_plot and self.df is not None:
            self.plot_selected()

    def _update_combobox(self, combo, values):
        """Update combobox values"""
        combo['values'] = values
        if values and combo.get() not in values:
            combo.set(values[0] if values else '')

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv'), ('All files', '*.*')])
        if not path:
            return

        # Try reading the CSV with several fallbacks to handle different delimiters
        df = None
        last_err = None
        
        # First, try to sniff delimiter with csv.Sniffer
        sep = None
        decimal_char = '.'
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                sample = f.read(4096)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                sep = dialect.delimiter
                # detect decimal comma in sample (e.g. '0,1' but not when comma is separator)
                if sep == ';' or (sep != ',' and bool(re.search(r"\d,\d", sample))):
                    decimal_char = ','
        except Exception:
            # If sniffing fails, check if semicolon is present (common French CSV format)
            try:
                with open(path, 'r', newline='', encoding='utf-8') as f:
                    sample = f.read(4096)
                    if ';' in sample:
                        sep = ';'
                        if bool(re.search(r"\d,\d", sample)):
                            decimal_char = ','
            except Exception:
                pass

        # Try reading with detected separator
        try:
            if sep:
                df = pd.read_csv(path, sep=sep, decimal=decimal_char)
            else:
                df = pd.read_csv(path)
        except Exception as e:
            last_err = e

        # If df has only one column, it might have been parsed incorrectly - retry with semicolon
        if df is not None and len(df.columns) == 1 and ';' in df.columns[0]:
            try:
                df = pd.read_csv(path, sep=';', decimal=',')
            except Exception as e:
                last_err = e
                df = None

        # Final fallback: use python engine with auto-detection
        if df is None:
            try:
                df = pd.read_csv(path, sep=None, engine='python', decimal=decimal_char)
            except Exception as e2:
                last_err = e2
                # Final attempt: skip bad lines
                try:
                    df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
                    messagebox.showwarning('Avertissement', 'Certaines lignes malformées ont été ignorées lors de la lecture.')
                except Exception as e3:
                    last_err = e3

        if df is None:
            messagebox.showerror('Erreur', f"Impossible de lire le fichier:\n{last_err}")
            return

        if df.empty:
            messagebox.showwarning('Vide', 'Le fichier CSV est vide.')
            return

        # Convert datetime columns to seconds (relative to first value)
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    # Check if it looks like a datetime with French format (dd/mm/yyyy HH:MM:SS,microseconds)
                    first_val = str(df[col].iloc[0])
                    if '/' in first_val and ':' in first_val:
                        # Custom parser for format: "30/01/2026 13:57:56,630000"
                        def parse_french_datetime(val):
                            try:
                                val_str = str(val)
                                # Replace comma with dot for microseconds
                                val_str = val_str.replace(',', '.')
                                # Parse with explicit format
                                return pd.to_datetime(val_str, format='%d/%m/%Y %H:%M:%S.%f')
                            except:
                                return pd.NaT
                        
                        datetime_col = df[col].apply(parse_french_datetime)
                        if datetime_col.notna().all():
                            # Convert to seconds from start
                            time_delta = (datetime_col - datetime_col.iloc[0]).dt.total_seconds()
                            df[col] = time_delta
                except Exception:
                    pass  # Keep original if conversion fails
        
        # Convert string columns with French decimal format (comma) to numeric
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    # Try to convert string with comma decimal to float
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
                except Exception:
                    pass  # Keep as string if conversion fails

        # Auto-create "Effort Z total (N)" if Z1, Z2, Z3 columns exist
        z_cols = ['Effort Z1 (N)', 'Effort Z2 (N)', 'Effort Z3 (N)']
        if all(col in df.columns for col in z_cols):
            df['Effort Z total (N)'] = df['Effort Z1 (N)'] + df['Effort Z2 (N)'] + df['Effort Z3 (N)']

        self.df = df
        self.loaded_file_path = path  # Store the path of loaded file
        cols = list(df.columns)

        # Calculate sampling frequency from first column (time column)
        try:
            if len(df) > 1:
                first_col = df.iloc[:, 0]  # First column
                time_diff = np.diff(first_col)
                mean_time_diff = np.mean(time_diff)
                if mean_time_diff > 0:
                    self.sampling_frequency = 1.0 / mean_time_diff
                else:
                    self.sampling_frequency = 1000  # Default if can't calculate
        except Exception:
            self.sampling_frequency = 1000  # Default sampling frequency

        # Update sampling frequency display and filter frequency field
        self.sampling_freq_label.config(text=f'{self.sampling_frequency:.0f} Hz')
        self.filter_freq_var.set(f'{self.sampling_frequency / 4:.2f}')  # Suggest Nyquist/4 as default cutoff

        # Update X/Y comboboxes. suspend auto-plot while populating
        self._suspend_auto_plot = True
        x_options = ['Index'] + cols
        self._update_combobox(self.x_combo, x_options)
        self.x_var.set('Index')

        # Update Y combobox: numeric columns only
        num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            # if no numeric columns, allow all columns
            num_cols = cols
        self._update_combobox(self.y_combo, num_cols)
        if num_cols:
            # set default without triggering plot
            self.y_var.set(num_cols[0])
        self._suspend_auto_plot = False
        
        # Update file label
        import os
        self.file_label.config(text=f'✅ {os.path.basename(path)}')
        self.index_label.config(text=f'📊 {len(df)} points • {len(cols)} colonnes')
        
        # Show compare button now that we have a file loaded
        self.compare_btn.pack(pady=3)
        
        # Reset compare mode when loading a new file
        if self.compare_mode:
            self.cancel_compare()
        
        # plot once with defaults
        try:
            self.plot_selected()
        except Exception:
            pass

    def load_compare_csv(self):
        """Load a second CSV file for comparison"""
        if self.df is None:
            messagebox.showwarning('Aucun fichier', 'Chargez d\'abord un fichier CSV principal.')
            return
        
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv'), ('All files', '*.*')])
        if not path:
            return

        # Read the CSV using the same logic as load_csv
        df = None
        sep = None
        decimal_char = '.'
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                sample = f.read(4096)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                sep = dialect.delimiter
                if sep == ';' or (sep != ',' and bool(re.search(r"\d,\d", sample))):
                    decimal_char = ','
        except Exception:
            try:
                with open(path, 'r', newline='', encoding='utf-8') as f:
                    sample = f.read(4096)
                    if ';' in sample:
                        sep = ';'
                        if bool(re.search(r"\d,\d", sample)):
                            decimal_char = ','
            except Exception:
                pass

        try:
            if sep:
                df = pd.read_csv(path, sep=sep, decimal=decimal_char)
            else:
                df = pd.read_csv(path)
        except Exception as e:
            messagebox.showerror('Erreur', f"Impossible de lire le fichier:\n{e}")
            return

        if df is None or df.empty:
            messagebox.showwarning('Vide', 'Le fichier CSV est vide.')
            return

        # If df has only one column, retry with semicolon
        if len(df.columns) == 1 and ';' in df.columns[0]:
            try:
                df = pd.read_csv(path, sep=';', decimal=',')
            except Exception:
                pass

        # Convert datetime columns to seconds (same logic as load_csv)
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    first_val = str(df[col].iloc[0])
                    if '/' in first_val and ':' in first_val:
                        def parse_french_datetime(val):
                            try:
                                val_str = str(val).replace(',', '.')
                                return pd.to_datetime(val_str, format='%d/%m/%Y %H:%M:%S.%f')
                            except:
                                return pd.NaT
                        datetime_col = df[col].apply(parse_french_datetime)
                        if datetime_col.notna().all():
                            time_delta = (datetime_col - datetime_col.iloc[0]).dt.total_seconds()
                            df[col] = time_delta
                except Exception:
                    pass

        # Convert string columns with French decimal format
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
                except Exception:
                    pass

        # Auto-create "Effort Z total (N)" if Z1, Z2, Z3 columns exist
        z_cols = ['Effort Z1 (N)', 'Effort Z2 (N)', 'Effort Z3 (N)']
        if all(col in df.columns for col in z_cols):
            df['Effort Z total (N)'] = df['Effort Z1 (N)'] + df['Effort Z2 (N)'] + df['Effort Z3 (N)']

        # Check if columns match the original file
        original_cols = set(self.df.columns)
        compare_cols = set(df.columns)
        
        if original_cols != compare_cols:
            # Show which columns are different
            missing_in_compare = original_cols - compare_cols
            extra_in_compare = compare_cols - original_cols
            msg = "Les colonnes du fichier de comparaison ne correspondent pas au fichier original.\n\n"
            if missing_in_compare:
                msg += f"Colonnes manquantes: {', '.join(list(missing_in_compare)[:5])}\n"
            if extra_in_compare:
                msg += f"Colonnes supplémentaires: {', '.join(list(extra_in_compare)[:5])}"
            messagebox.showerror('Colonnes incompatibles', msg)
            return

        # Store comparison data
        self.df_compare = df
        self.compare_file_path = path
        self.compare_mode = True
        
        # Update UI: show compare label and cancel button, hide filter and export sections
        import os
        self.compare_label.config(text=f'🔄 {os.path.basename(path)}')
        self.compare_label.pack(pady=2)
        self.cancel_compare_btn.pack(pady=3)
        
        # Hide filter and export sections
        self.filter_section.pack_forget()
        self.filter_frame.pack_forget()
        self.export_section.pack_forget()
        self.export_frame.pack_forget()
        
        # Hide compare button (already comparing)
        self.compare_btn.pack_forget()
        
        # Replot with comparison
        self.plot_selected()

    def cancel_compare(self):
        """Cancel comparison mode and return to single file view"""
        self.compare_mode = False
        self.df_compare = None
        self.compare_file_path = None
        self.x_data_compare = None
        self.y_data_compare = None
        
        # Hide compare-related UI
        self.compare_label.config(text='')
        self.compare_label.pack_forget()
        self.cancel_compare_btn.pack_forget()
        
        # Show compare button again
        self.compare_btn.pack(pady=3)
        
        # Show filter and export sections again
        self.filter_section.pack(fill=tk.X, padx=15, pady=(10, 3))
        self.filter_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        self.export_section.pack(fill=tk.X, padx=15, pady=(10, 3))
        self.export_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        # Replot without comparison
        self.plot_selected()

    def plot_selected(self):
        if self.df is None:
            messagebox.showwarning('Aucun fichier', 'Chargez d\u00e9abord un fichier CSV.')
            return

        x_choice = self.x_var.get()
        y_choice = self.y_var.get()
        if not y_choice:
            messagebox.showwarning('Aucune mesure', 'Sélectionnez une mesure (axe Y).')
            return

        try:
            if x_choice == 'Index':
                x = self.df.index
            else:
                x = self.df[x_choice]
            y = self.df[y_choice]

            self.ax.clear()
            self._style_axes()
            
            # Get file names for legend
            import os
            file1_name = os.path.basename(self.loaded_file_path) if self.loaded_file_path else 'Fichier 1'
            
            # Check if we're in comparison mode
            if self.compare_mode and self.df_compare is not None:
                # Plot first file
                self.ax.plot(x, y, linestyle='-', label=file1_name, color='#1565C0', linewidth=1.5)
                
                # Get data from comparison file
                if x_choice == 'Index':
                    x_compare = self.df_compare.index
                else:
                    x_compare = self.df_compare[x_choice]
                y_compare = self.df_compare[y_choice]
                
                # Store comparison data
                self.x_data_compare = np.asarray(x_compare)
                self.y_data_compare = np.asarray(y_compare)
                
                # Plot second file with different color
                file2_name = os.path.basename(self.compare_file_path) if self.compare_file_path else 'Fichier 2'
                self.ax.plot(x_compare, y_compare, linestyle='-', label=file2_name, color='#D32F2F', linewidth=1.5)
            else:
                self.ax.plot(x, y, linestyle='-', label='Original', color='#1565C0', linewidth=1)
            
            # Store data for index selection
            self.x_data = np.asarray(x)
            self.y_data = np.asarray(y)
            self.y_filtered = None  # Reset filtered data
            self.y_choice = y_choice  # Store column name
            self.x_is_index = (x_choice == 'Index')
            self.selected_indices = []  # Reset selected indices
            
            self.ax.set_xlabel(x_choice, fontsize=10)
            self.ax.set_ylabel(y_choice, fontsize=10)
            
            if self.compare_mode:
                self.ax.set_title(f'{y_choice} - Comparaison', fontsize=12, fontweight='bold', color=COLORS['text'])
            else:
                self.ax.set_title(f'{y_choice}', fontsize=12, fontweight='bold', color=COLORS['text'])
            
            self.ax.legend(loc='upper right', facecolor=COLORS['bg_medium'], 
                          edgecolor=COLORS['border'], labelcolor=COLORS['text'])
            self.fig.tight_layout()
            self.canvas.draw()
            
            # Update status and min/max
            if self.compare_mode and self.y_data_compare is not None:
                self.index_label.config(text=f'🔄 Comparaison: {len(self.x_data)} vs {len(self.x_data_compare)} points')
                # Show min/max for each curve separately (X and Y)
                x1_min, x1_max = np.nanmin(self.x_data), np.nanmax(self.x_data)
                x2_min, x2_max = np.nanmin(self.x_data_compare), np.nanmax(self.x_data_compare)
                y1_min, y1_max = np.nanmin(self.y_data), np.nanmax(self.y_data)
                y2_min, y2_max = np.nanmin(self.y_data_compare), np.nanmax(self.y_data_compare)
                self.minmax_label.config(text=f'X1: [{x1_min:.2f}, {x1_max:.2f}] X2: [{x2_min:.2f}, {x2_max:.2f}]  |  Y1: [{y1_min:.2f}, {y1_max:.2f}] Y2: [{y2_min:.2f}, {y2_max:.2f}]')
            else:
                self.index_label.config(text=f'📊 {len(self.x_data)} points')
                x_min, x_max = np.nanmin(self.x_data), np.nanmax(self.x_data)
                y_min, y_max = np.nanmin(self.y_data), np.nanmax(self.y_data)
                self.minmax_label.config(text=f'X: [{x_min:.2f}, {x_max:.2f}]  |  Y: [{y_min:.2f}, {y_max:.2f}]')
            
            # Save base limits for reset
            try:
                self._base_xlim = self.ax.get_xlim()
                self._base_ylim = self.ax.get_ylim()
            except Exception:
                self._base_xlim = None
                self._base_ylim = None
        except Exception as e:
            messagebox.showerror('Erreur', f"Impossible de tracer :\n{e}")

    def _handle_click(self, event):
        # Only active when X is 'Index'
        if not self.x_is_index or self.x_data is None or self.y_data is None:
            return
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        # Find closest point to click - use a copy to avoid modifying original
        try:
            x_copy = np.array(self.x_data, dtype=float)
            y_copy = np.array(self.y_data, dtype=float)
            xy_disp = self.ax.transData.transform(np.column_stack([x_copy, y_copy]))
            d = np.hypot(xy_disp[:, 0] - event.x, xy_disp[:, 1] - event.y)
            idx = int(np.argmin(d))
        except Exception:
            return

        # Display index if click is close enough (threshold: 10 pixels)
        if d[idx] < 10:
            # Add or remove index from selection (toggle or max 2)
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            elif len(self.selected_indices) < 2:
                self.selected_indices.append(idx)

            # Update label
            if len(self.selected_indices) == 0:
                self.index_label.config(text='')
            elif len(self.selected_indices) == 1:
                self.index_label.config(text=f'Début : Index {self.selected_indices[0]}')
            else:
                self.index_label.config(text=f'Début : Index {self.selected_indices[0]} | Fin : Index {self.selected_indices[1]}')
        else:
            # Reset selection when clicking outside of any point
            self.selected_indices = []
            self.index_label.config(text='')

    def _on_mouse_press(self, event):
        # Record press and prepare rectangle for left button
        self._press_event = event
        self._is_dragging = False
        if event.inaxes != self.ax:
            return
        if event.button == 1:
            # start rectangle
            try:
                self._zoom_rect = Rectangle((event.xdata, event.ydata), 0, 0,
                                            fill=False, color='gray', linestyle='--')
                self.ax.add_patch(self._zoom_rect)
                self.canvas.draw_idle()
            except Exception:
                self._zoom_rect = None

    def _on_mouse_move(self, event):
        # Update rectangle during drag
        if self._press_event is None or self._zoom_rect is None:
            return
        if event.inaxes != self.ax:
            return
        self._is_dragging = True
        x0, y0 = self._press_event.xdata, self._press_event.ydata
        x1, y1 = event.xdata, event.ydata
        if x0 is None or x1 is None:
            return
        xmin = min(x0, x1)
        ymin = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        self._zoom_rect.set_bounds(xmin, ymin, width, height)
        self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        # Handle release: zoom, reset or click
        if event.inaxes != self.ax:
            # cleanup
            if self._zoom_rect is not None:
                try:
                    self._zoom_rect.remove()
                except Exception:
                    pass
                self._zoom_rect = None
            self._press_event = None
            self._is_dragging = False
            self.canvas.draw_idle()
            return

        # Right click: reset to base limits
        if event.button == 3:
            if self._base_xlim is not None and self._base_ylim is not None:
                try:
                    self.ax.set_xlim(self._base_xlim)
                    self.ax.set_ylim(self._base_ylim)
                except Exception:
                    self.ax.relim()
                    self.ax.autoscale()
            else:
                self.ax.relim()
                self.ax.autoscale()
            if self._zoom_rect is not None:
                try:
                    self._zoom_rect.remove()
                except Exception:
                    pass
                self._zoom_rect = None
            # reset any index selection as well
            try:
                self.selected_indices = []
                self.index_label.config(text='')
            except Exception:
                pass
            self._press_event = None
            self._is_dragging = False
            self.canvas.draw()
            return

        # Left button release: zoom if dragged, otherwise treat as click
        if event.button == 1:
            if self._is_dragging and self._press_event is not None and self._zoom_rect is not None:
                x0, y0 = self._press_event.xdata, self._press_event.ydata
                x1, y1 = event.xdata, event.ydata
                if None in (x0, x1, y0, y1):
                    # cleanup
                    try:
                        self._zoom_rect.remove()
                    except Exception:
                        pass
                    self._zoom_rect = None
                    self._press_event = None
                    self._is_dragging = False
                    self.canvas.draw_idle()
                    return
                xmin, xmax = sorted([x0, x1])
                ymin, ymax = sorted([y0, y1])
                # Apply new limits
                try:
                    self.ax.set_xlim(xmin, xmax)
                    self.ax.set_ylim(ymin, ymax)
                except Exception:
                    pass
                # Map rectangle X-range to nearest data indices and update selection
                try:
                    if self.x_data is not None and len(self.x_data) > 0:
                        x_arr = np.asarray(self.x_data)
                        # handle possible non-numeric by attempting subtraction
                        try:
                            mask = (x_arr >= xmin) & (x_arr <= xmax)
                            inds = np.nonzero(mask)[0]
                        except Exception:
                            # fallback: compute nearest indices to bounds
                            inds = np.array([])
                        if inds.size >= 2:
                            sel0 = int(inds[0])
                            sel1 = int(inds[-1])
                        elif inds.size == 1:
                            sel0 = sel1 = int(inds[0])
                        else:
                            # no points exactly inside: pick nearest to xmin/xmax
                            try:
                                sel0 = int(np.argmin(np.abs(x_arr - xmin)))
                                sel1 = int(np.argmin(np.abs(x_arr - xmax)))
                            except Exception:
                                sel0 = sel1 = None
                        if sel0 is not None and sel1 is not None:
                            self.selected_indices = sorted([sel0, sel1])
                            # update label
                            if len(self.selected_indices) == 1:
                                self.index_label.config(text=f'Début : Index {self.selected_indices[0]}')
                            else:
                                self.index_label.config(text=f'Début : Index {self.selected_indices[0]} | Fin : Index {self.selected_indices[1]}')
                except Exception:
                    pass
                # remove rectangle
                try:
                    self._zoom_rect.remove()
                except Exception:
                    pass
                self._zoom_rect = None
                self._press_event = None
                self._is_dragging = False
                self.canvas.draw()
                return
            else:
                # treat as click (index selection)
                try:
                    self._handle_click(event)
                except Exception:
                    pass
                if self._zoom_rect is not None:
                    try:
                        self._zoom_rect.remove()
                    except Exception:
                        pass
                    self._zoom_rect = None
                self._press_event = None
                self._is_dragging = False
                self.canvas.draw_idle()
                return

    def apply_filter(self):
        """Apply Butterworth lowpass filter to the Y data"""
        if self.y_data is None:
            messagebox.showwarning('Aucune donnée', 'Tracez d\'abord un graphique.')
            return

        try:
            freq_cutoff = float(self.filter_freq_var.get())
            if freq_cutoff <= 0:
                messagebox.showerror('Erreur', 'La fréquence doit être positive.')
                return
        except ValueError:
            messagebox.showerror('Erreur', 'Entrez une fréquence valide (nombre).')
            return

        try:
            # Design Butterworth filter (order 4, normalized frequency)
            # Use calculated sampling frequency
            fs = self.sampling_frequency
            normalized_cutoff = freq_cutoff / (fs / 2)
            
            # Ensure normalized frequency is between 0 and 1
            if normalized_cutoff >= 1:
                messagebox.showwarning('Avertissement', f'La fréquence de coupure ({freq_cutoff} Hz) est trop élevée pour la fréquence d\'échantillonnage ({fs:.1f} Hz). Diminuez la valeur en dessous de {fs/2:.1f} Hz.')
                normalized_cutoff = 0.99
            
            if normalized_cutoff <= 0:
                messagebox.showerror('Erreur', 'La fréquence normalisée doit être positive.')
                return
            
            # Design the filter
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            
            # Handle NaN values: interpolate them before filtering
            y_to_filter = self.y_data.copy()
            nan_mask = np.isnan(y_to_filter)
            if np.any(nan_mask):
                # Interpolate NaN values
                valid_indices = np.where(~nan_mask)[0]
                nan_indices = np.where(nan_mask)[0]
                if len(valid_indices) > 0:
                    y_to_filter[nan_mask] = np.interp(nan_indices, valid_indices, y_to_filter[valid_indices])
            
            # Apply the filter
            y_filtered = signal.filtfilt(b, a, y_to_filter)
            self.y_filtered = y_filtered
            
            # Redraw with filtered data
            x_choice = self.x_var.get()
            x = self.x_data

            self.ax.clear()
            self._style_axes()
            
            # Plot original first, then filtered on top with thicker line
            self.ax.plot(x, self.y_data, linestyle='-', label='Original', 
                        color='#90CAF9', alpha=0.7, linewidth=0.8)
            self.ax.plot(x, y_filtered, linestyle='-', label=f'Filtré ({freq_cutoff} Hz)', 
                        color='#D32F2F', linewidth=2, zorder=10)

            self.ax.set_xlabel(x_choice, fontsize=10)
            self.ax.set_ylabel(self.y_choice, fontsize=10)
            self.ax.set_title(f'{self.y_choice} (filtré à {freq_cutoff} Hz)', 
                             fontsize=12, fontweight='bold', color=COLORS['text'])
            self.ax.legend(loc='upper right', facecolor=COLORS['bg_medium'], 
                          edgecolor=COLORS['border'], labelcolor=COLORS['text'])
            
            # Force auto-scale to show both curves
            self.ax.relim()
            self.ax.autoscale_view()
            
            self.fig.tight_layout()

            # Force redraw
            self.canvas.draw()
            self.canvas.flush_events()
            
            # Update status and min/max (showing filtered values)
            self.index_label.config(text=f'✅ Filtre: {freq_cutoff} Hz')
            x_min, x_max = np.nanmin(self.x_data), np.nanmax(self.x_data)
            y_min, y_max = np.nanmin(y_filtered), np.nanmax(y_filtered)
            self.minmax_label.config(text=f'X: [{x_min:.2f}, {x_max:.2f}]  |  Y filtré: [{y_min:.2f}, {y_max:.2f}]')

            # Update base limits to include both curves
            try:
                self._base_xlim = self.ax.get_xlim()
                self._base_ylim = self.ax.get_ylim()
            except Exception:
                self._base_xlim = None
                self._base_ylim = None

        except Exception as e:
            messagebox.showerror('Erreur', f"Impossible d'appliquer le filtre:\n{e}")

    def export_csv(self):
        if self.df is None:
            messagebox.showwarning('Aucun fichier', 'Veuillez d\'abord charger un fichier CSV.')
            return

        # Extract base filename from loaded file path
        import os
        if self.loaded_file_path:
            base_filename = os.path.splitext(os.path.basename(self.loaded_file_path))[0]
        else:
            base_filename = 'export'

        # Check conditions for export
        # Determine if we have a selection
        has_selection = len(self.selected_indices) >= 2
        is_filtered_export = self.export_filtered_var.get()
        
        # If not filtered and no selection, error
        if not is_filtered_export and not has_selection:
            messagebox.showwarning('Sélection incomplète', 'Veuillez sélectionner deux points (Début et Fin).')
            return
        
        # Extract data based on selection and filter status
        if has_selection:
            # Get begin and end indices (sort them)
            idx1, idx2 = sorted(self.selected_indices)
            begin_idx = idx1
            end_idx = idx2
            
            # Extract data between indices (inclusive)
            try:
                exported_df = self.df.iloc[begin_idx:end_idx + 1].copy()
            except Exception as e:
                messagebox.showerror('Erreur', f"Impossible d'extraire les données :\n{e}")
                return
            
            if is_filtered_export:
                default_filename = f'{base_filename}_filtré_{begin_idx}_{end_idx}.csv'
            else:
                default_filename = f'{base_filename}_{begin_idx}_{end_idx}.csv'
        else:
            # Filtered export without selection: use all data
            try:
                exported_df = self.df.copy()
            except Exception as e:
                messagebox.showerror('Erreur', f"Impossible de copier les données :\n{e}")
                return
            
            default_filename = f'{base_filename}_filtré_complet.csv'

        # Ask user for save location
        # If filtered export, include cutoff frequency in default filename
        if is_filtered_export:
            try:
                _freq = float(self.filter_freq_var.get())
                freq_str = "{:g}".format(_freq).replace('.', 'p')
            except Exception:
                freq_str = str(self.filter_freq_var.get()).replace('.', 'p')
            if has_selection:
                default_filename = f"{base_filename}_filtré_{freq_str}_{begin_idx}_{end_idx}.csv"
            else:
                default_filename = f"{base_filename}_filtré_{freq_str}_complet.csv"

        save_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            initialfile=default_filename
        )

        if not save_path:
            return

        # Check if filtered export is requested
        if self.export_filtered_var.get():
            # Apply filter to all numeric columns
            try:
                freq_cutoff = float(self.filter_freq_var.get())
                if freq_cutoff <= 0:
                    messagebox.showerror('Erreur', 'Veuillez entrer une fréquence valide pour le filtrage.')
                    return
                
                # Design filter
                fs = self.sampling_frequency
                normalized_cutoff = freq_cutoff / (fs / 2)
                if normalized_cutoff >= 1:
                    normalized_cutoff = 0.99
                
                b, a = signal.butter(4, normalized_cutoff, btype='low')
                
                # Get numeric columns (skip first column which is time)
                numeric_cols = [c for c in exported_df.columns if pd.api.types.is_numeric_dtype(exported_df[c])]
                if len(exported_df.columns) > 0:
                    # Skip first column (time) in numeric columns to filter
                    numeric_cols = [c for c in numeric_cols if c != exported_df.columns[0]]
                
                # Apply filter to each numeric column and add filtered version
                for col in numeric_cols:
                    filtered_data = signal.filtfilt(b, a, exported_df[col].values)
                    exported_df[f'{col}_filtré'] = filtered_data
                
            except ValueError:
                messagebox.showerror('Erreur', 'Entrez une fréquence valide (nombre).')
                return
            except Exception as e:
                messagebox.showerror('Erreur', f"Impossible d'appliquer le filtre :\n{e}")
                return

        # Save the exported data
        try:
            exported_df.to_csv(save_path, index=False)
            if self.export_filtered_var.get():
                messagebox.showinfo('Succès', f'Fichier exporté avec filtrage :\n{save_path}\n\n{len(exported_df)} lignes sauvegardées avec colonnes filtrées.')
            else:
                messagebox.showinfo('Succès', f'Fichier exporté avec succès :\n{save_path}\n\n{len(exported_df)} lignes sauvegardées.')
        except Exception as e:
            messagebox.showerror('Erreur', f"Impossible de sauvegarder le fichier :\n{e}")


if __name__ == '__main__':
    root = tk.Tk()
    app = CsvPlotApp(root)
    root.mainloop()
