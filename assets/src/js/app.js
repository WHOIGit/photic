import $ from 'jquery';
import 'what-input';
import  SelectionArea from '@simonwep/selection-js';
import 'jquery-datetimepicker';
import Tagify from '@yaireo/tagify';
import Toastify from 'toastify-js'
import moment, { localeData } from 'moment';
import 'select2';

// Foundation JS relies on a global variable. In ES6, all imports are hoisted
// to the top of the file so if we used `import` to import Foundation,
// it would execute earlier than we have assigned the global variable.
// This is why we have to use CommonJS require() here since it doesn't
// have the hoisting behavior.
window.jQuery = $;
window.$ = $;

require('datatables.net-zf');
require('datatables.net-buttons-zf');
require('datatables.net-buttons/js/buttons.colVis.js');
require('datatables.net-buttons/js/buttons.html5.js');
require('datatables.net-colreorder-zf');
require('datatables.net-fixedcolumns-zf');
require('datatables.net-fixedheader-zf');
require('datatables.net-rowgroup-zf');
require('datatables.net-searchpanes-zf');
window.moment = require('moment');

const $panel = $("#main-panel");
const $container = $("#roi-container-wrapper");
const $container_inner = $("#roi-container");

$('#filter-before-date').datetimepicker({
    inline: false,
    format: 'm/d/Y H:i',
    formatTime: 'H:i',
    formatDate: 'm/d/Y',
});

$('#filter-after-date').datetimepicker({
    inline: false,
    format: 'm/d/Y H:i',
    formatTime: 'H:i',
    formatDate: 'm/d/Y',
});

const selection = new SelectionArea({
    // All elements in this container can be selected
    selectables: ['#roi-container > img'],

    // The container is also the boundary in this case
    boundaries: ['#roi-container'],

    singleTap: {

        // Enable single-click selection (Also disables range-selection via shift + ctrl).
        allow: true,
        // 'native' (element was mouse-event target) or 'touch' (element visually touched).
        intersect: 'native'
    },
}).on('beforestart', ({store, event}) => {
    if((event.button == 2)) return false;
}).on('start', ({store, event}) => {
    // Remove class if the user isn't pressing the control key or ⌘ key
    if (!event.ctrlKey && !event.metaKey) {

        // Unselect all elements
        for (const el of store.stored) {
            el.classList.remove('selected');
        }

        // Clear previous selection
        selection.clearSelection();
    }
}).on('move', ({store: {changed: {added, removed}}}) => {

    // Add a custom class to the elements that where selected.
    for (const el of added) {
        el.classList.add('selected');
    }

    // Remove the class from elements that where removed
    // since the last selection
    for (const el of removed) {
        el.classList.remove('selected');
    }
 }).on('stop', ({store, event}) => {
    selection.keepSelection()
    $(store.selected).addClass('selected');
    $(store.changed.removed).removeClass('selected');
});

$("body").on('contextmenu', function(ev) {
    hideTags();
});
$("body").on('click', function(ev) {
    if(!$(ev.target).is("#tag-holder")){
        hideTags();
    }
});

function getCsrfToken() {
    return $('[name="csrfmiddlewaretoken"]').val();
}

function getFilters() {
    let filters = {}
    filters["annotator"] = $("#filter-annotator").val();
    filters["label"] =  $("#filter-label").val()!=null ? $("#filter-label").val() : getQueryParam("label");
    filters['collection'] = $('#filter-collection').val();
    filters['sortby'] = $('#filter-sortby').val();
    return filters;

}
function getQueryParam(name){
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
    
}
let sortbyValue = getQueryParam('sortby');
if(sortbyValue){
    $("#filter-sortby").val(sortbyValue);
}

$("#filter-sortby").on('change', filterChange);
$("#filter-annotator").on('change', filterChange);
$("#filter-label").on('change', filterChange);
$("#filter-collection").on('change', filterChange);
$("#filter-button").on('click', filterChange);

$("#filter-collection").on('change', getLabels);
$("#labels_only_collection").on('change', getLabels);

function filterChange(ev){
    ev.preventDefault();
    $container_inner.empty()
    scrollPageNum = 1;
    let filters = getFilters();
    updateQuery(filters);
    loadPage(scrollPageNum)
};
function filterByLabel(label_name){
    $("#filter-label").val(label_name);
    $("#filter-label").trigger("change");
};

function getSelectedWrapper(){
    return selection.getSelection();
}
$("#add_to_collection_form").on('submit', function(ev){
    ev.preventDefault();
    addCollectionSubmit();
});

function addCollectionSubmit(){
    let selected_rois = getSelectedWrapper();
    let collection_name = $("#add_to_collection_select").val();
    
    let rois = [];
    for (let i=0; i<selected_rois.length; i++){
        let roi_id = $(selected_rois[i]).data("roi-id");
        rois.push(roi_id);
    }
    let current_collection_name = null;
    if($("#add_to_collection_remove").is(':checked')){
        current_collection_name = $("#filter-collection").val();
    }
    $.ajax({
        url: '/api/move_or_copy_to_collection',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        data: JSON.stringify({
            'collection_name': collection_name,
            'delete_from_collection_name': current_collection_name,
            'rois': rois,
        }),
        success: add_to_collection_callback,
    });
};
function add_to_collection_callback(evt){
    let selected_rois = getSelectedWrapper();
    for (let i=0; i<selected_rois.length; i++){
        if($("#add_to_collection_remove").is(':checked')){
            $(selected_rois[i]).fadeOut();
        }else{
            $(selected_rois[i]).fadeTo(200, 0.2).fadeTo(200, 1).fadeTo(200, 0.2).fadeTo(200, 1);
        }
    }
    if(evt.collection_created){
        showMessage(`New Collection "${evt.collection_created}" created`);
    }
    showMessage("ROIs added to Collection");
    getCollections();
}
$("#apply-label-form").on('submit', function(ev){
    ev.preventDefault();
    applyLabelSubmit();
});

function applyLabelSubmit(){
    let selected_rois = getSelectedWrapper();
    if (selected_rois.length==0) return;
    let label_name = $("#apply_label_select").val();
    if(!label_name){
        return false;
    }
    let annotations = [];
    for (let i=0; i<selected_rois.length; i++){
        let roi = $(selected_rois[i]).data("roi-id");
        annotations.push({label:label_name, roi_id: roi});
    }
    $.ajax({
        url: '/api/create_or_verify_annotations',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        data: JSON.stringify({
            'annotations': annotations,
        }),
        success: apply_label_callback,
    });

    pushRecentLabel(label_name);
};
let lastHiddenROIs = [];
function apply_label_callback(evt){
    let selected_rois = getSelectedWrapper();
    for (let i=0; i<selected_rois.length; i++){
        if($("#apply_label_hide").is(':checked')){
            $(selected_rois[i]).fadeOut();
        }else{
            $(selected_rois[i]).fadeTo(200, 0.2).fadeTo(200, 1).fadeTo(200, 0.2).fadeTo(200, 1);
        }
    }

    if($("#apply_label_hide").is(':checked')){
        lastHiddenROIs.push(selected_rois);

        $("#unhide_last").removeClass("disabled");
    }
}

let REGEX_ALPHANUMERIC = /^[a-zA-Z0-9_ ]+$/i;
$("#add-label-form").on("keyup", function(ev){
    testField(REGEX_ALPHANUMERIC, $("#add-label-form"), $('#add_label_text'));
});

function testField(regex, form, field){
    if(regex.test($(field).val())){
        form.foundation('removeErrorClasses', field);
        return true;
    }else{
        form.foundation('addErrorClasses', field);
        return false;
    }
}

function getLabels(evt){
    let data = {};
    if($("#labels_only_collection").is(':not(:checked)')){
        data['collection'] = $('#filter-collection').val();
    }
    $.post('api/get_labels', data, get_labels_callback);
}
let LABEL_LIST;
function get_labels_callback(r){
    if(r.labels){
        LABEL_LIST = r.labels;
        buildLabelSelect();
    }
}
function buildLabelSelect(){

    let $filter_label = $('#filter-label');
    let $apply_label_select = $('#apply_label_select');
    $filter_label.empty();
    $apply_label_select.empty();

    let filterBy = getQueryParam('label');
    
    $filter_label.append('<option value="">All</option><option value="unlabeled">unlabeled</option>');
    $apply_label_select.append('<option value="">- Select a Label -</option>');

    let recent_labels = getRecentLabels();
    if(recent_labels){
        for (let i=0; i<recent_labels.length; i++){
            let label_name = recent_labels[i];
            let selected = i==0?'selected':'';
            $apply_label_select.append($(`<option ${selected} value="${label_name}" > ${label_name} </option>`));
        }
    }
    $apply_label_select.append('<option value="">━━━━━━━━━━━━━━━━</option>');

    for (let i=0; i<LABEL_LIST.length; i++){
        let label_name = LABEL_LIST[i].label_name;
        let selected = filterBy==label_name?'selected':'';
        let has_winning_class = LABEL_LIST[i].has_winning?'class="has_winning"':'';
        $filter_label.append($(`<option ${selected} value="${label_name}" ${has_winning_class} > ${label_name} </option>`));
        $apply_label_select.append($(`<option ${selected} value="${label_name}" ${has_winning_class} > ${label_name} </option>`));
    }
}

function getCollections(){
    $.post('api/get_collections', {}, get_collections_callback);
}
function get_collections_callback(r){
    if(r.collections){
        let $filter_collection = $('#filter-collection');
        $filter_collection.empty();

        let filterBy = getQueryParam('collection');

        for (let i=0; i<r.collections.length; i++){
            let collection_name = r.collections[i];
            let selected = filterBy==collection_name?'selected':'';
            $filter_collection.append($(`<option ${selected} value="${collection_name}" > ${collection_name} </option>`));
        }
    }
}


$("#next_label").on('click', nextLabel);
$("#prev_label").on('click', prevLabel);



function nextLabel(){
    nextLabelLoop($('#filter-label option:selected'));
}
function nextLabelLoop($ele){
    let $next = $ele.next();
    if($next.length==0){
        $next = $('#filter-label option').first();
    }
    if(!$next.hasClass('has_winning') && $('#filter-label option.has_winning').length>0){
        nextLabelLoop($next);
    }else{
        $next.prop('selected', true).change();
    }
}

function prevLabel(){
    prevLabelLoop($('#filter-label option:selected'));
}
function prevLabelLoop($ele){
    let $prev = $ele.prev();
    if($prev.length==0){
        $prev = $('#filter-label option').last();
    }
    if(!$prev.hasClass('has_winning') && $('#filter-label option.has_winning').length>0){
        prevLabelLoop($prev);
    }else{
        $prev.prop('selected', true).change();
    }
    
}

$(document).on('keypress', function(event) {
    if ($(event.target).closest("input,textarea")[0]) {
        return;
    }
    let key = event.key.toUpperCase();
    if(key == 'N'){
        nextLabel();
    }else if( key ==='P'){
        prevLabel();
    }else if( key ==='ENTER'){
        $("#apply-label-form").trigger('submit');
    }
});

$("#unhide-last-form").on('submit', function(ev){
    ev.preventDefault();
    let last = lastHiddenROIs.pop();
    if(last){
        $(last).fadeIn();
    }
    if(lastHiddenROIs){
        $("#unhide_last").addClass("disabled");
    }
});

$("#add-label-form").on('submit', function(ev){
    ev.preventDefault();
    if(testField(REGEX_ALPHANUMERIC, $("#add-label-form"), $('#add_label_text'))){
        let label_name = $("#add_label_text").val()
        $.post('api/create_label', {
            'name': label_name,
        },
            add_label_callback
        )
        $("#add_label_text").val('');
    }
})
function add_label_callback(r){
    if(r.created){
        showMessage("Label created");
    }else{

        showError("Label already exists");
    }
    getLabels();
}

function showMessage(msg, error=false){
    Toastify({
        text: msg,
        offset: {
            x: 15, // horizontal axis - can be a number or a string indicating unity. eg: '2em'
            y: 60 // vertical axis - can be a number or a string indicating unity. eg: '2em'
          },
        duration: 3000,
        newWindow: true,
        close: true,
        gravity: "top", // `top` or `bottom`
        position: "right", // `left`, `center` or `right`
        backgroundColor: error?"crimson":"seagreen",
        stopOnFocus: true, // Prevents dismissing of toast on hover
      }).showToast();

}
function showError(msg){
    showMessage(msg, true);
}
let recent_labels_max = 5;
function getRecentLabels(){
    return JSON.parse(window.localStorage.getItem('recent_labels')||"[]");
}
function pushRecentLabel(value){
    let recent_labels = getRecentLabels();
    let index = recent_labels.indexOf(value);
    if(index!=-1){
        recent_labels.splice(index, 1);
    }
    recent_labels.unshift(value);
    while(recent_labels.length>recent_labels_max){
        recent_labels.pop();
    }
    window.localStorage.setItem('recent_labels', JSON.stringify(recent_labels));

    buildLabelSelect();
}
function updateQuery(obj){
    let url = new URL(document.location);
    let search_params = url.searchParams;
    for (const key in obj){
        search_params.set(key, obj[key]);
    }
    url.search = search_params.toString();
    window.localStorage.setItem('search_params', url.search);
    window.history.pushState({path:url.toString()},'',url.toString());
}

$(".homeLink").on("click", function(evt){
    evt.preventDefault();
   
    let url = new URL(document.location);
    url.pathname = '';
    let query = window.localStorage.getItem('search_params');
    if(query){
        url.search = query;
    }
    document.location = url.toString();

});

let $overlay = $("#tag-holder");
let $dt = $overlay.find("table").DataTable( {
    data: [],
    paging: false,
    searching: false,
    info: false,
    columns: [
        { 
            title: "Label",
            render: function(data, type, row) {
                return `<a class="filterByLabel" data-label-id="${data}"> ${data} </a>`;
            }
        },
        { title: "Annotator" },
        { 
            title: "Time",
            render: function(data, type, row) {
                return moment(data).format('YYYY-MM-DD h:mma Z');
            }
        },
        { title: 'Verifications' },
    ]
} );

function showAnnotations(event, rows, roi_id) {
    let posX = event.pageX;
    let posY = event.pageY;

    let overlayWidth = $overlay.outerWidth();
    //show the menu directly over the placeholder
    $overlay.css({
        position: "absolute",
        top: 15+posY + "px",
        left: (posX -(overlayWidth/2)) + "px"
    })
    $overlay.show();
    $overlay.find(".roi_id span").html(roi_id);
    $dt.clear();
    $dt.rows.add(rows);
    $dt.draw(); 
}

$('body').on('click', '.filterByLabel', function(ev) {
    ev.preventDefault();
    filterByLabel($(ev.target).data('label-id'));
});

function hideTags(event) {
    $overlay.hide();
}

$container.on('contextmenu', 'img', function(ev) {
    ev.preventDefault();
    $.post('api/roi_annotations', {
        'roi_id': $(ev.target).data('roi-id'),
    }, function(r) {
        showAnnotations(ev, r.rows, r.roi_id);
    });
    return false;
});

$(document).ajaxSend(function(event, jqXHR, ajaxOptions) {
  let csrf = getCsrfToken();
  if (csrf != null) {
    jqXHR.setRequestHeader('X-CSRFToken', csrf);
  }
});

function loadROIs(filters={}){
    $.post(
        'api/roi_list',
        filters,
        handleRoiAjax
    )
    showLoader(true);
}
let scrollPageNum = 1;
let morePages = true;
let imagesOutstanding = 0;
function showLoader(show){
    if(show){
        $("#roi-container-loader").addClass("visible");
    }else{
        $("#roi-container-loader").removeClass("visible");
    }
}
function imageLoaded(evt) {
    imagesOutstanding--;
    if(imagesOutstanding==0){
        allowLoad = true;
        showLoader(false);
        checkWindowFull();
    }
}
function checkWindowFull(){//keep loading pages of ROIs until the screen is filled and a scroll bar is present
    if($container.height() < $panel.height() && morePages){
        scrollPageNum++;
        loadPage(scrollPageNum);
    }
}
function handleRoiAjax(r) {
    if(r.roi_count!=0){
        for (let i=0;i< r.rois.length; i++) {
            imagesOutstanding++;
            let $img = $('<img class="image-tile infinite-item" draggable="false" data-roi-id="' + r.rois[i].id + '" src="' + r.rois[i].path + '" />');
            $img.on("load", imageLoaded);
            $container_inner.append($img);
        }
    }else{
        showLoader(false);
    }

    $("#roi_count").html("<h5>" + r.roi_count + " ROI(s) found</h5>")
    $("#roi_count").show();

    morePages = r.has_next_page;
}
$(window).on("load", function() {
});
let allowLoad = true;
function onScroll(){
    if(morePages&&allowLoad){
        let s = $panel.scrollTop(),
        d = $container.height(),
        c = $panel.height();

        let scrollPercent = (s / (d - c)) * 100;
        if(scrollPercent>99){
            scrollPageNum++;
            allowLoad = false;
            loadPage(scrollPageNum);
        }

    }
};
$panel.on("scroll", onScroll);

require('foundation-sites');

let $add_label_text = new Foundation.Abide($("#add_label_text"), {});

Foundation.Abide.defaults.patterns['alpha_numeric_score_space'] = REGEX_ALPHANUMERIC

$('.largeOptionSetSelection').select2({
    theme: "foundation"
});
$('.largeOptionSetSelectionTag').select2({
    theme: "foundation",
    tags:true
});

$(document).foundation();

getLabels();

function loadPage(num){
    let filters = getFilters();
    filters["page"] = num;
    loadROIs(filters);
}

loadPage(scrollPageNum);

