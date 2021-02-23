import $ from 'jquery';
import 'what-input';
import  SelectionArea from '@simonwep/selection-js';
import Bricks from 'bricks.js';
import 'jquery-datetimepicker';
import Tagify from '@yaireo/tagify';
import moment from 'moment';

// Foundation JS relies on a global variable. In ES6, all imports are hoisted
// to the top of the file so if we used `import` to import Foundation,
// it would execute earlier than we have assigned the global variable.
// This is why we have to use CommonJS require() here since it doesn't
// have the hoisting behavior.
window.jQuery = $;
window.$ = $;

var dt = require('datatables');

const sizes = [
    { columns: 2, gutter: 10 },                   // assumed to be mobile, because of the missing mq property
    { mq: '768px', columns: 3, gutter: 25 },
    { mq: '1024px', columns: 6, gutter: 25 }
  ]
  
  // create an instance
  
  const instance = Bricks({
    container: '.bricks-container',
    packed:    'data-packed',        // if not prefixed with 'data-', it will be added
    sizes:     sizes
  })
  
  // bind callbacks
  
  instance
    .on('pack',   () => console.log('ALL grid items packed.'))
    .on('update', () => console.log('NEW grid items packed.'))
    .on('resize', size => console.log('The grid has be re-packed to accommodate a new BREAKPOINT.'))
  
  // start it up, when the DOM is ready
  // note that if images are in the grid, you may need to wait for document.readyState === 'complete'
  document.onreadystatechange = function () {
    if(document.readyState === "complete"){
    instance
      .resize(true)     // bind resize handler
      .pack()           // pack initial items
    }
  }
  
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
    selectables: ['.bricks-container > img'],

    // The container is also the boundary in this case
    boundaries: ['#main-panel'],

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


$(".bricks-container img").on('contextmenu', function(ev) {
    ev.preventDefault();
    showTags(ev);
    return false;
});

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
    ]
} );

function showTags(event){
    // let $targ = $(el);
    // let width = $targ.outerWidth();
    // let height = $targ.outerHeight();
    let dataSet = $(event.target).data("tags");

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
    if(dataSet && dataSet.length>0){
        $dt.rows.add( dataSet ).draw();
    }

}
require('foundation-sites');

// If you want to pick and choose which modules to include, comment out the above and uncomment
// the line below
//import './lib/foundation-explicit-pieces';


$(document).foundation();
