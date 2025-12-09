import streamlit as st
import pandas as pd
import csv
from io import StringIO

# Initialize or update session state variables if not present
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'totals' not in st.session_state:
    st.session_state.totals = {}
if 'temp_expense' not in st.session_state:
    st.session_state.temp_expense = {}
if 'form_values' not in st.session_state:
    st.session_state.form_values = {"item_name": "", "total_cost": 0.0, "split_method": "Equal", "selected_people": []}

def recalculate_totals(expenses, people):
    totals = {person: {'total': 0, 'items': []} for person in people}
    for expense in expenses:
        item = expense['name']
        cost = expense['cost']
        if expense['split_method'] == 'Equal':
            split_cost = cost / len(expense['selected_people'])
            for person in expense['selected_people']:
                totals[person]['total'] += split_cost
                totals[person]['items'].append((item, split_cost))
        elif expense['split_method'] == 'Weighted':
            total_quantity = sum(expense['quantities'].values())
            for person, quantity in expense['quantities'].items():
                person_cost = (quantity / total_quantity) * cost
                totals[person]['total'] += person_cost
                totals[person]['items'].append((item, person_cost))
    return totals

def generate_csv(totals):
    csv_file = StringIO()
    fieldnames = ['Person', 'Total', 'Items']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for person, data in totals.items():
        items_str = "; ".join([f"{item}: ${cost:.2f}" for item, cost in data['items']])
        writer.writerow({'Person': person, 'Total': f"{data['total']:.2f}", 'Items': items_str})
    return csv_file.getvalue()

def reset_form_values():
    st.session_state.form_values = {"item_name": "", "total_cost": 0.0, "split_method": "Equal", "selected_people": []}

def calculate_total_expense(expenses):
    return sum(expense['cost'] for expense in expenses)

def cost_splitter_app():
    st.title("Cost Splitter for Shared Purchases")

    # Enter People
    people_input = st.text_input("Enter names (comma-separated)")
    if people_input:
        st.session_state.people = [name.strip() for name in people_input.split(',')]
    else:
        st.session_state.people = []

    # Expense fields
    item_name = st.text_input("Item Name", value=st.session_state.form_values['item_name'])
    total_cost = st.number_input("Total Cost", format="%.2f", value=st.session_state.form_values['total_cost'])
    split_method = st.radio("Splitting Method", ['Equal', 'Weighted'],
                            index=['Equal', 'Weighted'].index(st.session_state.form_values['split_method']))

    # Checkbox selection instead of a multiselect
    selected_people = []
    st.write("Select People:")
    for person in st.session_state.people:
        checked = st.checkbox(
            person,
            value=(person in st.session_state.form_values['selected_people']),
            key=f"chk_{person}"
        )
        if checked:
            selected_people.append(person)

    # NEXT button
    if st.button("Next"):
        if split_method == 'Weighted':
            st.session_state.temp_expense = {
                'name': item_name,
                'cost': total_cost,
                'split_method': split_method,
                'selected_people': selected_people
            }
            st.session_state.form_values['split_method'] = split_method
        else:
            st.session_state.expenses.append({
                'name': item_name,
                'cost': total_cost,
                'split_method': split_method,
                'selected_people': selected_people
            })
            st.session_state.totals = recalculate_totals(
                st.session_state.expenses, st.session_state.people
            )
            reset_form_values()

    # Weighted quantity entry
    if st.session_state.get('temp_expense'):
        quantities = {
            person: st.number_input(
                f"Quantity for {person}:",
                min_value=0.0,
                value=1.0,
                format="%.2f",
                key=f"qty_{person}"
            )
            for person in st.session_state.temp_expense['selected_people']
        }

        if st.button("Add Expense with Quantities"):
            st.session_state.expenses.append({
                **st.session_state.temp_expense,
                'quantities': quantities
            })
            st.session_state.temp_expense = {}
            st.session_state.totals = recalculate_totals(
                st.session_state.expenses, st.session_state.people
            )
            reset_form_values()

    # Display total expense
    total_expense = calculate_total_expense(st.session_state.expenses)
    st.write(f"Total Expense: ${total_expense:.2f}")

    # Show totals
    if st.session_state.totals:
        for person, data in st.session_state.totals.items():
            st.write(f"{person}: ${data['total']:.2f}")

    # Delete expense
    expense_names = [expense['name'] for expense in st.session_state.expenses]
    selected_expense_to_delete = st.selectbox("Select an expense to delete:", [""] + expense_names)

    if st.button("Delete Expense"):
        if selected_expense_to_delete:
            st.session_state.expenses = [
                expense for expense in st.session_state.expenses
                if expense['name'] != selected_expense_to_delete
            ]
            st.session_state.totals = recalculate_totals(
                st.session_state.expenses, st.session_state.people
            )

    # CSV export
    if st.button("Export to CSV"):
        csv_data = generate_csv(st.session_state.totals)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="cost_splits.csv",
            mime='text/csv'
        )

cost_splitter_app()
