const drop_btn = document.querySelector(".drop-btn span");
const menu_wrapper = document.querySelector(".wrapper");
const menu_bar = document.querySelector(".menu-bar");
//const setting_drop = document.querySelector(".setting-drop");
const help_drop = document.querySelector(".help-drop");
//const setting_item = document.querySelector(".setting-item");
const help_item = document.querySelector(".help-item");
const setting_btn = document.querySelector(".back-setting-btn");
const help_btn = document.querySelector(".back-help-btn");

drop_btn.onclick = (()=>{
    menu_wrapper.classList.toggle("show");
});

//setting_item.onclick = (()=>{
//    menu_bar.style.marginLeft = "-319px";
//    setTimeout(()=>{
//        setting_drop.style.display = "block";
//    }, 100);
//});

help_item.onclick = (()=>{
    menu_bar.style.marginLeft = "-319px";
    setTimeout(()=>{
        help_drop.style.display = "block";
    }, 100);
    menu_bar.style.height = "170px";
});

setting_btn.onclick = (()=>{
    menu_bar.style.marginLeft = "0px";
    setting_drop.style.display = "none";
});

help_btn.onclick = (()=>{
    help_drop.style.display = "none";
    menu_bar.style.marginLeft = "0px";
    menu_bar.style.height = "fit-content";
});