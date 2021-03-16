'use strict';

let addButton = document.querySelector("#add-address-line");
let totalForms = document.querySelector("#id_form-TOTAL_FORMS");
let addressFormset = document.querySelectorAll("#address p");
let container = document.querySelector("#address");
let countrySelects = document.querySelectorAll("#address select");
let selectWithChangeHandler = []

let formNum = 1 ? totalForms == null : totalForms.value - 1;

addButton.addEventListener('click', addForm);

function processSelection() {
    countrySelects = document.querySelectorAll("#address select")
    countrySelects.forEach(
        function (node) {
            if (node.name.endsWith('country')) {
                if (!selectWithChangeHandler.includes(node)) {
                    selectWithChangeHandler.push(node)
                    node.addEventListener('change', function handleSelect() {
                        state_url = $('#Url').attr('data-url').replace(0, node.value)
                        node_name = node.name.split('-');
                        state_id = 'id_' + node_name[0] + '-' + node_name[1] + '-state';
                        let state = $("#" + state_id);
                        state.empty()
                        $.ajax({
                            method: 'GET',
                            url: state_url,
                            dataType: 'json'
                        }).done(function (data) {
                            data = $.parseJSON(data);
                            data.forEach(function (d) {
                                state.append(`<option value="${d['pk']}">
                                       ${d['fields']['name']}
                                  </option>`);
                            });
                        });
                    });
                }
            }
        }
    )
}

processSelection()

function addForm(e) {

    e.preventDefault();

    let formRegex = RegExp(`form-(\\d){1}-`, 'g') //Regex to find all instances of the form number

    formNum++
    for (let i = 0; i < addressFormset.length; i++) {
        let newNode = addressFormset[i].cloneNode(true) //Clone the bird form
        newNode.innerHTML = newNode.innerHTML.replace(formRegex, `form-${formNum}-`)
        container.insertBefore(newNode, addButton)
    }

    if (totalForms != null)
        totalForms.setAttribute('value', `${formNum + 1}`)
    processSelection()
}
