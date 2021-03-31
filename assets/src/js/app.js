import $ from 'jquery';
import 'what-input';
import  SelectionArea from '@simonwep/selection-js';
import 'jquery-datetimepicker';
import Tagify from '@yaireo/tagify';
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

const $panel= $("#main-panel");
const $container= $("#roi-container");

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

$container.on('contextmenu', 'img', function(ev) {
    ev.preventDefault();
    $.post('api/roi_annotations', {
        'roi_id': $(ev.target).data('roi-id'),
    }, function(r) {
        showAnnotations(ev, r.rows);
    });
    return false;
});

function getFilters() {
    let filters = {}
    filters["annotator"] = $("#filter-annotator").val();
    filters["label"] = $("#filter-label").val();
    filters['collection'] = $('#filter-collection').val();
    return filters;

}

$("#filter-button").on('click', function(ev){
    ev.preventDefault();
    $container.empty()
    scrollPageNum = 1;
    let filters = getFilters();
    updateQuery(filters);
    loadPage(1)
});

// $('#filter-collection').select(function(ev) {
//     ev.preventDefault();
//     updateFilters();
// });
function getSelectedWrapper(){
    return selection.getSelection();
}
$("#apply_label").on('click', function(ev){
    ev.preventDefault();
    let selected_rois = getSelectedWrapper();
    let label_name = $("#apply_label_select").val();
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
});

function apply_label_callback(evt){
    let selected_rois = getSelectedWrapper();
    for (let i=0; i<selected_rois.length; i++){
        if($("#add_label_hide").is(':checked')){
            $(selected_rois[i]).fadeOut();
        }else{
            $(selected_rois[i]).fadeTo(200, 0.2).fadeTo(200, 1).fadeTo(200, 0.2).fadeTo(200, 1);
        }
    }

}

$("#add_label").on('click', function(ev){
    ev.preventDefault();
    let label_name = $("#add_label_text").val()
    let re = /^[a-z0-9_ ]+$/i;
    
    if(!re.test(label_name)){
        alert("label characters can only be alphanumeric, [underscore], or [space]");   
    }
    
    $.post('api/create_label', {
        'name': label_name,
    },
        function(r) {
            console.log(r)
            //add to select element here
        }
    )

})

function add_label_callback(evt){

}

function updateQuery(obj){
    var url = new URL(document.location);
    var search_params = url.searchParams;
    for (const key in obj){
        search_params.set(key, obj[key]);
    }

    url.search = search_params.toString();

    window.history.pushState({path:url.toString()},'',url.toString());
}

let $overlay = $("#tag-holder");
let $dt = $overlay.find("table").DataTable( {
    data: [],
    paging: false,
    searching: false,
    info: false,
    columns: [
        { title: "Label" },
        { title: "Annotator" },
        { title: "Time" },
        { title: 'Verifications' },
    ]
} );

function showAnnotations(event, rows) {
    let posX = event.pageX;
    let posY = event.pageY;

    let overlayWidth = $overlay.outerWidth();
    //show the menu directly over the placeholder
    $overlay.css({
        position: "absolute",
        top: posY + "px",
        left: (posX -(overlayWidth/2)) + "px"
    })
    $overlay.show();
    $dt.clear();
    if(rows && rows.length>0) {
        $.each(rows, function(i, row) {
            row[2] = moment(row[2]).format('YYYY-MM-DD h:mma Z');
            $dt.rows.add([row]);
        });
        $dt.draw();
    }
}

function hideTags(event) {
    $overlay.hide();
}

function create_or_verify_annotation(roi_id, label_name, annotator_name, callback) {
    $.ajax({
        url: '/api/create_or_verify_annotations',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        data: JSON.stringify({
            'annotator': annotator_name,
            'annotations': [{
                'roi_id': roi_id,
                'label': label_name,
            }],
        }),
        success: callback,
    });
}

require('foundation-sites');

// If you want to pick and choose which modules to include, comment out the above and uncomment
// the line below
//import './lib/foundation-explicit-pieces';

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
}
let scrollPageNum = 1;
let morePages = true;

function handleRoiAjax(r) {
    if(r.rois){

        for (let i=0;i< r.rois.length; i++) {
            $container.append('<img class="image-tile infinite-item" draggable="false" data-roi-id="' + r.rois[i].id + '" src="' + r.rois[i].path + '" />')
        }
    }

    $("#roi_count").html("<h5>" + r.roi_count + " ROI(s) found</h5>")
    $("#roi_count").show();

    morePages = r.has_next_page;
}
$panel.on("scroll", function(){
    if(morePages){
    let s = $panel.scrollTop(),
     d = $container.height(),
     c = $panel.height();

    let scrollPercent = (s / (d - c)) * 100;
    if(scrollPercent>99){
        scrollPageNum++;
        loadPage(scrollPageNum);
    }

}
});

function loadPage(num){
    let filters = getFilters();
    filters["page"] = num;
    loadROIs(filters);
}

loadPage(scrollPageNum);

$('.largeOptionSetSelection').select2({
    theme: "foundation"
});

$(document).foundation();
