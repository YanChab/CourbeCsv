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


class CsvPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Visualiseur CSV de mesures (v2)')
        self.df = None

        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        btn_load = tk.Button(top, text='Charger CSV', command=self.load_csv)
        btn_load.pack(side=tk.LEFT)

        tk.Label(top, text='X:').pack(side=tk.LEFT, padx=(10, 2))
        self.x_var = tk.StringVar(value='Index')
        self.x_menu = tk.OptionMenu(top, self.x_var, 'Index')
        self.x_menu.config(width=20)
        self.x_menu.pack(side=tk.LEFT)

        tk.Label(top, text='Y:').pack(side=tk.LEFT, padx=(10, 2))
        self.y_var = tk.StringVar(value='')
        self.y_menu = tk.OptionMenu(top, self.y_var, '')
        self.y_menu.config(width=30)
        self.y_menu.pack(side=tk.LEFT)

        # 'Tracer' button removed: plotting is now automatique lors du changement d'axes

        # Filtering controls
        tk.Label(top, text='Fréq. échant.:').pack(side=tk.LEFT, padx=(10, 2))
        self.sampling_freq_label = tk.Label(top, text='- Hz', width=10, anchor='w')
        self.sampling_freq_label.pack(side=tk.LEFT)
        
        tk.Label(top, text='Coupure (Hz):').pack(side=tk.LEFT, padx=(10, 2))
        self.filter_freq_var = tk.StringVar(value='1.0')
        filter_entry = tk.Entry(top, textvariable=self.filter_freq_var, width=10)
        filter_entry.pack(side=tk.LEFT, padx=2)
        
        btn_filter = tk.Button(top, text='Appliquer filtre', command=self.apply_filter)
        btn_filter.pack(side=tk.LEFT, padx=6)

        # Matplotlib figure
        self.fig = Figure(figsize=(7, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        # Label to display selected index (only active when X='Index')
        self.index_label = tk.Label(root, text='', font=('Arial', 10), fg='black', bg='white')
        self.index_label.pack(side=tk.BOTTOM, padx=6, pady=6)

        # Export controls frame
        export_frame = tk.Frame(root)
        export_frame.pack(side=tk.BOTTOM, padx=6, pady=3)
        
        self.export_filtered_var = tk.BooleanVar(value=False)
        checkbox_filtered = tk.Checkbutton(export_frame, text='Filtré', variable=self.export_filtered_var)
        checkbox_filtered.pack(side=tk.LEFT, padx=(0, 6))

        # Export button
        self.export_btn = tk.Button(export_frame, text='Exporter CSV', command=self.export_csv)
        self.export_btn.pack(side=tk.LEFT)

        # Track plot state for index selection
        self.x_data = None
        self.y_data = None
        self.y_filtered = None  # Store filtered data
        self.x_is_index = False
        self.selected_indices = []  # List to store up to 2 selected indices
        self.y_choice = None  # Store the current Y column name
        self.sampling_frequency = 1000  # Default sampling frequency (Hz)
        self.loaded_file_path = None  # Store the path of the loaded CSV file
        self._suspend_auto_plot = False

        # Mouse/zoom state
        self._zoom_rect = None
        self._press_event = None
        self._is_dragging = False
        self._base_xlim = None
        self._base_ylim = None

        # Connect mouse events (press, move, release)
        self.fig.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.fig.canvas.mpl_connect('button_release_event', self._on_mouse_release)

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

        # Update X/Y menus. suspend auto-plot while populating
        self._suspend_auto_plot = True
        x_options = ['Index'] + cols
        self._update_option_menu(self.x_menu, self.x_var, x_options)

        # Update Y menu: numeric columns only
        num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            # if no numeric columns, allow all columns
            num_cols = cols
        self._update_option_menu(self.y_menu, self.y_var, num_cols)
        if num_cols:
            # set default without triggering plot
            self.y_var.set(num_cols[0])
        self._suspend_auto_plot = False
        # plot once with defaults
        try:
            self.plot_selected()
        except Exception:
            pass

        messagebox.showinfo('Chargé', f'Fichier chargé : {path}\nColonnes trouvées: {len(cols)}')

    def _update_option_menu(self, menu_widget, var, options):
        menu = menu_widget['menu']
        menu.delete(0, 'end')
        for opt in options:
            menu.add_command(label=opt, command=lambda v=opt, vr=var: self._option_selected(vr, v))
        # set default; if auto-plot is not suspended, use _option_selected to trigger plot
        if options:
            if getattr(self, '_suspend_auto_plot', False):
                var.set(options[0])
            else:
                self._option_selected(var, options[0])

    def _option_selected(self, var, value):
        # set the option and update plot
        var.set(value)
        if getattr(self, '_suspend_auto_plot', False):
            return
        try:
            self.plot_selected()
        except Exception:
            pass

    def plot_selected(self):
        if self.df is None:
            messagebox.showwarning('Aucun fichier', 'Chargez d\u00e9abord un fichier CSV.')
            return

        x_choice = self.x_var.get()
        y_choice = self.y_var.get()
        if not y_choice:
            messagebox.showwarning('Aucune mesure', 'S\u00e9lectionnez une mesure (axe Y).')
            return

        try:
            if x_choice == 'Index':
                x = self.df.index
            else:
                x = self.df[x_choice]
            y = self.df[y_choice]

            self.ax.clear()
            self.ax.plot(x, y, linestyle='-', label='Original', color='blue')
            
            # Store data for index selection
            self.x_data = np.asarray(x)
            self.y_data = np.asarray(y)
            self.y_filtered = None  # Reset filtered data
            self.y_choice = y_choice  # Store column name
            self.x_is_index = (x_choice == 'Index')
            self.selected_indices = []  # Reset selected indices
            self.index_label.config(text='')  # Clear label
            
            self.ax.set_xlabel(x_choice)
            self.ax.set_ylabel(y_choice)
            self.ax.set_title(f'{y_choice} vs {x_choice}')
            self.ax.grid(True)
            self.ax.legend()
            self.fig.tight_layout()
            self.canvas.draw()
            # Save base limits for reset
            # Save base limits for reset
            try:
                self._base_xlim = self.ax.get_xlim()
                self._base_ylim = self.ax.get_ylim()
            except Exception:
                self._base_xlim = None
                self._base_ylim = None
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
            # Plot original first, then filtered on top with thicker line
            self.ax.plot(x, self.y_data, linestyle='-', label='Original', color='blue', alpha=0.4, linewidth=0.5)
            self.ax.plot(x, y_filtered, linestyle='-', label=f'Filtré ({freq_cutoff} Hz)', color='red', linewidth=2, zorder=10)

            self.ax.set_xlabel(x_choice)
            self.ax.set_ylabel(self.y_choice)
            self.ax.set_title(f'{self.y_choice} vs {x_choice} (avec filtre)')
            self.ax.grid(True)
            self.ax.legend()
            
            # Force auto-scale to show both curves
            self.ax.relim()
            self.ax.autoscale_view()
            
            self.fig.tight_layout()

            # Force redraw
            self.canvas.draw()
            self.canvas.flush_events()

            # Update base limits to include both curves
            try:
                self._base_xlim = self.ax.get_xlim()
                self._base_ylim = self.ax.get_ylim()
            except Exception:
                self._base_xlim = None
                self._base_ylim = None

            messagebox.showinfo('Succès', f'Filtre passe-bas Butterworth appliqué\nFréquence de coupure: {freq_cutoff} Hz')
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
