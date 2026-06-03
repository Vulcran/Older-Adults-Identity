function generateYahooAdHTML(data) {
    const {
        searchTerm,
        blueText,
        description,
        imagePath,
        isRandomImage,
        companyName,
        formattedLink,
        isOfficialSite,
        isAd
    } = data;

    const imageIsRandom = Boolean(isRandomImage) || imagePath === "https://picsum.photos/200";
    const faviconSize = imageIsRandom ? 28 : 34;

    let adHeader = isAd ? `
    <li class="first">
        <div class="dd mb-16 AdHdrTop">
            <div class="compTitle">
                <h2 class="title mb-0">
                    <a style="float:none;padding-left:0px;color:#444444;" class="fz-13 lh-m" target="_blank" referrerpolicy="unsafe-url" href="https://help.yahoo.com/kb/search/SLN2244.html">Ad</a>
                </h2> 
                <span class="stxt ">
                    <span class="fz-13 lh-m">related to: ${searchTerm}</span>
                </span>
            </div>
        </div>
    </li>` : "";

    let officialSiteBadge = isOfficialSite ? `
        <span style="cursor: pointer !important; display: inline-block !important; visibility: visible !important; opacity: 1 !important; float: none !important; vertical-align: 3px; height: 17px; line-height: 17px; margin-left: 8px; padding: 0 6px; box-sizing: border-box; white-space: nowrap; color: #333; background-color: #eee; border-radius: 2px; font-size: 11px; font-weight: 500;">Official Site</span>
    ` : "";

    return `
<ol class="reg scta searchCenterTopAds">
    ${adHeader}
    <li class="last">
        <div class="dd fst lst ads bcan1 relsrch AdTop" style="cursor: pointer;">
            <div class="layoutMiddle">
                <div class="compTitle mb-2">
                    <a class="d-b bcan1cb" target="_blank" referrerpolicy="unsafe-url" href="#">
                        <div class="p-abs">
                            <div class="thmb ad-favicon bd-1-E3E3E3 bdr-100 lh-32 bgc-4th mr-8 va-mid" style="display: inline-flex; align-items: center; justify-content: center; width: 28px !important; height: 28px !important; min-width: 28px; min-height: 28px; padding: 0 !important; overflow: hidden; border-radius: 50%; box-sizing: border-box;">
                                <img class="s-img p-rel ov-h va-top bgc-4th" width="${faviconSize}" height="${faviconSize}" alt="" src="${imagePath}" aria-hidden="true" role="presentation" style="display: block; visibility: visible; opacity: 1; width: ${faviconSize}px !important; height: ${faviconSize}px !important; min-width: ${faviconSize}px; min-height: ${faviconSize}px; max-width: none; max-height: none; object-fit: cover; border-radius: ${imageIsRandom ? "50%" : "0"};">
                            </div>
                            <span style="color: #5a5a5a; letter-spacing: 0.195px;" class="ad-domain d-ib va-mid fz-13 fc-dustygray lh-16 s-url fw-m">
                                <span class="d-b fc-141414">${companyName}</span>${formattedLink}
                            </span>
                        </div>
                        <h3 class="title d-b pt-38 td-hu va-top mxw-100p" style="display: block !important; width: 100%; max-width: 100%; box-sizing: border-box; overflow: visible; white-space: normal;">
                            <span class="fz-20 lh-24 fw-500 ls-027 d-ib tc" style="display: inline !important; overflow-wrap: anywhere;">${blueText}</span>
                            ${officialSiteBadge}
                        </h3>
                    </a>
                </div>
                <div class="layoutCenter acl-b">
                    <div class="compText aAbs">
                        <p class="fz-14 fc-dustygray lh-22 ls-02 mah-44 mb-2 ov-h d-box fbox-ov fbox-lc2">${description}</p>
                    </div>
                </div>
                <div style="clear:both"></div>
            </div>
            <div class="layoutBottom"></div>
        </div>
    </li>
</ol>`;
}
