'use strict';

let createAddressBtn = $("#add-address-line");
let createEarningBtn = $("#add-earning-line");
let employeeIDGeneratorBtn = $("#employee-id-gen");

let dateInputs = $("input[name*=date")
let tabMenu = $(".tab-menu a");


tabMenu.click((event) => {
    event.preventDefault();
    let activeMenu = $(".active-menu");
    activeMenu.removeClass('active-menu');
    let t = $(event.target);
    t.addClass("active-menu");
    let m = $(t.attr("href"));
    if (m.length) {
        let activeTab = $(".active-tab");
        activeTab.removeClass('active-tab');
        m.addClass("active-tab");
    }
});

createAddressBtn.click((event) => {
    event.preventDefault();
    let addressManagementFormSet = $("#address #id_form-TOTAL_FORMS");
    let formNum = parseInt(addressManagementFormSet.val());
    let addressRef = $(`#id_address-wrapper-${formNum - 1}`).clone();
    let formRegex = RegExp(`form-(\\d){1}-`, 'g'); //Regex to find all instances of the form number    
    addressRef[0].innerHTML = addressRef[0].innerHTML.replace(formRegex, `form-${formNum}-`);
    addressRef.attr("id", `id_address-wrapper-${formNum}`);
    $(addressRef).insertBefore(createAddressBtn);
    addressManagementFormSet.val(formNum + 1);
});

createEarningBtn.click((event) => {
    event.preventDefault();
    let earningManagementFormSet = $("#employee-earning #id_form-TOTAL_FORMS");
    let formNum = parseInt(earningManagementFormSet.val());
    let earningRef = $(`#id_earning-wrapper-${formNum - 1}`).clone();
    let formRegex = RegExp(`form-(\\d){1}-`, 'g');//Regex to find all instances of the form number    
    earningRef[0].innerHTML = earningRef[0].innerHTML.replace(formRegex, `form-${formNum}-`);
    let lineNum = earningRef.find("span.earning-line-num");
    lineNum.text(parseInt(lineNum.text()) + 1);
    earningRef.attr("id", `id_earning-wrapper-${formNum}`);
    earningManagementFormSet.val(formNum + 1);
    $(earningRef).insertBefore(createEarningBtn);
});

employeeIDGeneratorBtn.click((event) => {
    event.preventDefault();
    let input = $("input[name='employee_id_number']")
    input.val("20")
});

dateInputs.attr('autocomplete', 'off');
dateInputs.datepicker({
    dateFormat: "yy-mm-dd"
})




//function processSelection() {
    //countrySelects = document.querySelectorAll("#address select")
    //countrySelects.forEach(
        //function (node) {
            //if (node.name.endsWith('country')) {
                //if (!selectWithChangeHandler.includes(node)) {
                    //selectWithChangeHandler.push(node)
                    //node.addEventListener('change', function handleSelect() {
                        //state_url = $('#Url').attr('data-url').replace(0, node.value)
                        //node_name = node.name.split('-');
                        //state_id = 'id_' + node_name[0] + '-' + node_name[1] + '-state';
                        //let state = $("#" + state_id);
                        //state.empty()
                        //$.ajax({
                            //method: 'GET',
                            //url: state_url,
                            //dataType: 'json'
                        //}).done(function (data) {
                            //data = $.parseJSON(data);
                            //data.forEach(function (d) {
                                //state.append(`<option value="${d['pk']}">
                                       //${d['fields']['name']}
                                  //</option>`);
                            //});
                        //});
                    //});
                //}
            //}
        //}
    //)
//}

