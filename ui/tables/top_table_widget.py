from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QStyledItemDelegate, QMessageBox, QApplication
from PyQt6.QtGui import QKeyEvent, QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt
from .table_item_delegate import TableItemDelegate, UpperCaseItemDelegate
from ui.dialogs.progress_dialog import ProgressDialog

class TableWidget(QTableWidget):
    def __init__(self, rows, cols, parent=None):
        super().__init__(rows, cols, parent)
        self.setup_table()
        self.pasted_cells = []
        self.undo_stack = []
        self.redo_stack = []
        self.initial_state_saved = False
        self.programmatic_change = False
        self._updating_table = False
        self._updating_bottom_table = False

    def setup_table(self):
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked |
                             QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        if not self.programmatic_change:
            if not self.initial_state_saved:
                current_text = item.text()
                self.programmatic_change = True
                item.setText("")
                self.push_undo_state()
                item.setText(current_text)
                self.programmatic_change = False
                self.initial_state_saved = True
            
            row, col = item.row(), item.column()
            if col == 0 or (row == 1 and col >= 2):
                if item.text() != item.text().upper():
                    self.programmatic_change = True
                    item.setText(item.text().upper())
                    self.programmatic_change = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selection()
        elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.push_undo_state()
            self.paste_to_selection()
            self.select_pasted_cells()
        elif event.key() == Qt.Key.Key_Delete:
            self.push_undo_state()
            self.clear_selection()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_F2):
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                self.edit(current)
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.redo()
            else:
                self.undo()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.redo()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.redo()
        elif event.key() in range(Qt.Key.Key_0, Qt.Key.Key_9 + 1):
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                if event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                    self.edit(current)
                    if self.cellWidget(current.row(), current.column()):
                        self.cellWidget(
                            current.row(), current.column()).keyPressEvent(event)
                    return
            super().keyPressEvent(event)
        elif event.text() and not event.modifiers():
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                self.edit(current)
                if self.cellWidget(current.row(), current.column()):
                    self.cellWidget(current.row(), current.column()
                                    ).keyPressEvent(event)
                return
            super().keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            current = self.currentIndex()
            if current.isValid():
                if self.state() == QAbstractItemView.State.EditingState:
                    self.commitData(self.cellWidget(
                        current.row(), current.column()))
                    self.closePersistentEditor(
                        self.item(current.row(), current.column()))

                row, col = current.row(), current.column()
                if event.key() == Qt.Key.Key_Up:
                    row -= 1
                elif event.key() == Qt.Key.Key_Down:
                    row += 1
                elif event.key() == Qt.Key.Key_Left:
                    col -= 1
                elif event.key() == Qt.Key.Key_Right:
                    col += 1

                new_index = self.model().index(row, col)
                if new_index.isValid() and row < self.rowCount():
                    self.setCurrentIndex(new_index)
                    self.scrollTo(new_index)
                return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def save_state(self):
        state = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            state.append(row_data)
        return state

    def push_undo_state(self):
        if self.programmatic_change:
            return
            
        current_state = self.save_state()
        
        if self.undo_stack and current_state == self.undo_stack[-1]:
            return
            
        self.undo_stack.append(current_state)
        self.redo_stack = []
        
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
            
        current_state = self.save_state()
        self.redo_stack.append(current_state)
        
        previous_state = self.undo_stack.pop()
        self.restore_state(previous_state)
        
        if len(self.redo_stack) > 100:
            self.redo_stack.pop(0)

    def redo(self):
        if not self.redo_stack:
            return
            
        current_state = self.save_state()
        self.undo_stack.append(current_state)
        
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)
        
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def restore_state(self, state):
        self.programmatic_change = True
        self.blockSignals(True)
        
        try:
            for row in range(min(self.rowCount(), len(state))):
                for col in range(min(self.columnCount(), len(state[row]))):
                    item = self.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        self.setItem(row, col, item)
                    item.setText(state[row][col])
        finally:
            self.blockSignals(False)
            self.programmatic_change = False
            self.viewport().update()
            
            main_window = self.window()
            if hasattr(main_window, 'calculate_totals'):
                main_window.calculate_totals()

    def copy_selection(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted(index.row() for index in selection)
        cols = sorted(index.column() for index in selection)
        min_row, max_row = rows[0], rows[-1]
        min_col, max_col = cols[0], cols[-1]
        clipboard = QApplication.clipboard()
        text = ""
        for r in range(min_row, max_row + 1):
            row_text = []
            for c in range(min_col, max_col + 1):
                item = self.item(r, c)
                row_text.append(item.text() if item else "")
            text += "\t".join(row_text) + "\n"
        clipboard.setText(text.strip())

    def paste_to_selection(self):
        try:
            progress = ProgressDialog("Pasting Data", "Processing paste operation...", self)
            progress.show()
            QApplication.processEvents()
            progress.update_progress(5)

            selection = self.selectedIndexes()
            if not selection:
                progress.close()
                return

            first_row = selection[0].row()
            first_col = selection[0].column()
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            
            if not text.strip():
                progress.close()
                return

            rows = [row for row in text.split('\n') if row.strip()]
            grid = [row.split('\t') for row in rows]
            progress.update_progress(15)

            is_size_header_paste = (first_row == 1)
            if is_size_header_paste:
                is_vertical = all(len(row) == 1 for row in grid) and len(grid) > 1
                if is_vertical:
                    transposed = []
                    for i in range(len(grid[0])):
                        row_data = []
                        for j in range(len(grid)):
                            if i < len(grid[j]):
                                row_data.append(grid[j][i])
                            else:
                                row_data.append('')
                        transposed.append(row_data)
                    grid = transposed
            progress.update_progress(20)

            main_window = self.window()
            needed_rows = len(grid)
            needed_cols = max(len(row) for row in grid)
            current_editable_rows = self.rowCount() - 3
            current_editable_cols = self.columnCount() - 2

            rows_to_add = max(0, (first_row + needed_rows) - (current_editable_rows + 2))
            cols_to_add = max(0, (first_col + needed_cols) - (current_editable_cols + 2))
            progress.update_progress(25)

            if rows_to_add > 0 or cols_to_add > 0:
                progress.label.setText("Adjusting table size...")
                
                if hasattr(main_window, 'default_data_rows'):
                    main_window.default_data_rows += rows_to_add
                if hasattr(main_window, 'default_cols'):
                    main_window.default_cols += cols_to_add
                
                if hasattr(main_window, 'save_table_data'):
                    saved_data = main_window.save_table_data()
                progress.update_progress(40)
                
                if hasattr(main_window, 'setup_table'):
                    main_window.setup_table()
                progress.update_progress(45)
                
                if hasattr(main_window, 'restore_table_data'):
                    main_window.restore_table_data(saved_data)
                
                if hasattr(main_window, 'row_input'):
                    main_window.row_input.setText(str(main_window.default_data_rows))
                if hasattr(main_window, 'col_input'):
                    main_window.col_input.setText(str(main_window.default_cols - 2))
            
            progress.update_progress(50)
            progress.label.setText("Pasting data...")

            self.pasted_cells = []
            total_cells = len(grid) * max(len(row) for row in grid) if grid else 1
            processed_cells = 0
            
            self.programmatic_change = True
            
            try:
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        current_row = first_row + r
                        current_col = first_col + c

                        processed_cells += 1
                        if processed_cells % 10 == 0:
                            progress_val = 50 + (40 * processed_cells / total_cells)
                            progress.update_progress(min(90, int(progress_val)))
                            QApplication.processEvents()

                        if (current_row >= self.rowCount() or 
                            current_col >= self.columnCount() or
                            current_row == 0 or 
                            current_row == self.rowCount() - 1):
                            continue

                        if current_row != 1:
                            if current_col == 1:
                                if not value.isdigit() or not (1 <= int(value) <= 9):
                                    continue
                            elif current_col >= 2:
                                try:
                                    float(value)
                                except ValueError:
                                    continue

                        if not self.item(current_row, current_col):
                            self.setItem(current_row, current_col, QTableWidgetItem())

                        if current_col == 0 or (current_row == 1 and current_col >= 2):
                            self.item(current_row, current_col).setText(value.strip().upper())
                        else:
                            self.item(current_row, current_col).setText(value.strip())
                        
                        self.pasted_cells.append((current_row, current_col))
            finally:
                self.programmatic_change = False

            progress.update_progress(95)
            self.select_pasted_cells()
            
            if hasattr(main_window, 'calculate_totals'):
                main_window.calculate_totals()
            
            progress.update_progress(100)

        except Exception as e:
            QMessageBox.warning(self, "Paste Error", f"Failed to paste data: {str(e)}")
            if 'progress' in locals():
                progress.close()

    def select_pasted_cells(self):
        if not self.pasted_cells:
            return
        self.clearSelection()
        for row, col in self.pasted_cells:
            item = self.item(row, col)
            if item:
                item.setSelected(True)

    def clear_selection(self):
        for index in self.selectedIndexes():
            if index.row() == 0 or index.row() == self.rowCount() - 1:
                continue
            if self.item(index.row(), index.column()):
                self.item(index.row(), index.column()).setText("")