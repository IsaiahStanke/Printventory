(function() {
    let open = false;
    const devtools = /./;
    devtools.toString = function() {
        open = true;
        console.log("%cHey! What are you looking for? 👀", "color: red; font-size: 16px; font-weight: bold;");
    };
    console.log(devtools);
})();

console.log(`
    ██████╗ ██████╗ ██╗███╗   ██╗████████╗██╗   ██╗
    ██╔══██╗██╔══██╗██║████╗  ██║╚══██╔══╝██║   ██║
    ██████╔╝██████╔╝██║██╔██╗ ██║   ██║   ██║   ██║
    ██╔═══╝ ██╔══██╗██║██║╚██╗██║   ██║   ██║   ██║
    ██║     ██║  ██║██║██║ ╚████║   ██║   ╚██████╔╝
    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ 
    `);
    