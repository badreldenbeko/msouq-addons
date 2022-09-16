odoo.define('e_learning_custom.fullscreen', function (require) {
"use strict";

    var FullScreen = require('website_slides.fullscreen');
//    var VideoPlayer = require('website_slides.fullscreen').VideoPlayer;
    var core = require('web.core');
    var QWeb = core.qweb;
    var publicWidget = require('web.public.widget');
    var config = require('web.config');
    var Quiz = require('website_slides.quiz').Quiz;
    var session = require('web.session');

    var VideoPlayer = publicWidget.Widget.extend({
        template: 'website.slides.fullscreen.video',
        youtubeUrl: 'https://www.youtube.com/iframe_api',

        init: function (parent, slide) {
            this.slide = slide;
            return this._super.apply(this, arguments);
        },
        start: function (){
            var self = this;
            return Promise.all([this._super.apply(this, arguments), this._loadYoutubeAPI()]).then(function() {
                self._setupYoutubePlayer();
            });
        },
        _loadYoutubeAPI: function () {
            var self = this;
            var prom = new Promise(function (resolve, reject) {
                if ($(document).find('script[src="' + self.youtubeUrl + '"]').length === 0) {
                    var $youtubeElement = $('<script/>', {src: self.youtubeUrl});
                    $(document.head).append($youtubeElement);

                    // function called when the Youtube asset is loaded
                    // see https://developers.google.com/youtube/iframe_api_reference#Requirements
                    onYouTubeIframeAPIReady = function () {
                        resolve();
                    };
                } else {
                    resolve();
                }
            });
            return prom;
        },
        /**
         * Links the youtube api to the iframe present in the template
         *
         * @private
         */
        _setupYoutubePlayer: function (){
            this.player = new YT.Player('youtube-player' + this.slide.id, {
                playerVars: {
                    'autoplay': 1,
                    'origin': window.location.origin
                },
                events: {
                    'onStateChange': this._onPlayerStateChange.bind(this)
                }
            });
        },
        /**
         * Specific method of the youtube api.
         * Whenever the player starts playing/pausing/buffering/..., a setinterval is created.
         * This setinterval is used to check te user's progress in the video.
         * Once the user reaches a particular time in the video (30s before end), the slide will be considered as completed
         * if the video doesn't have a mini-quiz.
         * This method also allows to automatically go to the next slide (or the quiz associated to the current
         * video) once the video is over
         *
         * @private
         * @param {*} event
         */
        _onPlayerStateChange: function (event){
            var self = this;

            if (self.slide.completed) {
                return;
            }

            if (event.data !== YT.PlayerState.ENDED) {
                if (!event.target.getCurrentTime) {
                    return;
                }

                if (self.tid) {
                    clearInterval(self.tid);
                }

                self.currentVideoTime = event.target.getCurrentTime();
                self.totalVideoTime = event.target.getDuration();
                self.tid = setInterval(function (){
                    self.currentVideoTime += 1;
                    if (self.totalVideoTime && self.currentVideoTime > self.totalVideoTime - 30){
                        clearInterval(self.tid);
                        if (!self.slide.hasQuestion && !self.slide.completed){
                            self.trigger_up('slide_to_complete', self.slide);
                        }
                    }
                }, 1000);
            } else {
                if (self.tid) {
                    clearInterval(self.tid);
                }
                this.player = undefined;
                if (this.slide.hasNext) {
                    this.trigger_up('slide_go_next');
                }
            }
        },
    });

    FullScreen.include({
        _preprocessSlideData: function (slidesDataList) {
            slidesDataList.forEach(function (slideData, index) {
                // compute hasNext slide
                slideData.hasNext = index < slidesDataList.length-1;
                // compute embed url
                slideData.isPdf = parseInt($("span[data-id='" + slideData.id + "']")[0].innerText);
                if (slideData.type === 'url') {
                    slideData.embedCode = $(slideData.embedCode).attr('src') || ""; // embedCode contains an iframe tag, where src attribute is the url (youtube or embed document from odoo)
                    var separator = slideData.embedCode.indexOf("?") !== -1 ? "&" : "?";
                    var scheme = slideData.embedCode.indexOf('//') === 0 ? 'https:' : '';
                    var params = { rel: 0, enablejsapi: 1, origin: window.location.origin };
                    if (slideData.embedCode.indexOf("//drive.google.com") === -1) {
                        params.autoplay = 1;
                    }
                    slideData.embedUrl = slideData.embedCode ? scheme + slideData.embedCode + separator + $.param(params) : "";
                } else if (slideData.type === 'video') {
                    slideData.embedUrl = $(slideData.embedCode).find('source').attr('src') || ""; // embedCode contains an iframe tag, where src attribute is the url (youtube or embed document from odoo)
                } else if (slideData.type === 'infographic' || (slideData.type === 'document' && slideData.is_pdf)) {
                    slideData.embedUrl = _.str.sprintf('/web/image/slide.slide/%s/image_1024', slideData.id);
                } else if (_.contains(['document', 'presentation'], slideData.type) && !slideData.is_pdf) {
                    slideData.embedUrl = $(slideData.embedCode).attr('src');
                }
                // fill empty property to allow searching on it with _.filter(list, matcher)
                slideData.isQuiz = !!slideData.isQuiz;
                slideData.hasQuestion = !!slideData.hasQuestion;
                // technical settings for the Fullscreen to work
                slideData._autoSetDone = _.contains(['infographic', 'presentation', 'document', 'webpage'], slideData.type) && !slideData.hasQuestion;
            });
            return slidesDataList;
        },
        _renderSlide: function () {
            var slide = this.get('slide');
            var $content = this.$('.o_wslides_fs_content');
            $content.empty();

            // display quiz slide, or quiz attached to a slide
            if (slide.type === 'quiz' || slide.isQuiz) {
                $content.addClass('bg-white');
                var QuizWidget = new Quiz(this, slide, this.channel);
                return QuizWidget.appendTo($content);
            }

            // render slide content
            if (_.contains(['document', 'presentation', 'infographic', 'video'], slide.type)) {
                $content.html(QWeb.render('website.slides.fullscreen.content', {widget: this}));
            } else if (slide.type === 'url') {
                this.videoPlayer = new VideoPlayer(this, slide);
                return this.videoPlayer.appendTo($content);
            } else if (slide.type === 'webpage'){
                var $wpContainer = $('<div>').addClass('o_wslide_fs_webpage_content bg-white block w-100 overflow-auto');
                $(slide.htmlContent).appendTo($wpContainer);
                $content.append($wpContainer);
                this.trigger_up('widgets_start_request', {
                    $target: $content,
                });
            }
            return Promise.resolve();
        },
        _onChangeSlide: function () {
            var self = this;
            var slide = this.get('slide');
            self._pushUrlState();
            return this._fetchSlideContent().then(function() { // render content
                var websiteName = document.title.split(" | ")[1]; // get the website name from title
                document.title =  (websiteName) ? slide.name + ' | ' + websiteName : slide.name;
                if  (config.device.size_class < config.device.SIZES.MD) {
                    self._toggleSidebar(); // hide sidebar when small device screen
                }
                return self._renderSlide();
            }).then(function() {
                if (slide._autoSetDone && !session.is_website_user) {  // no useless RPC call
                    if (['document', 'presentation', 'url'].includes(slide.type)) {
                        // only set the slide as completed after iFrame is loaded to avoid concurrent execution with 'embedUrl' controller
                        if (self.el.querySelector('iframe.o_wslides_iframe_viewer') != undefined)
                            self.el.querySelector('iframe.o_wslides_iframe_viewer').addEventListener('load', () => self._setCompleted(slide.id));
                    } else {
                           return self._setCompleted(slide.id);
                    }
                }
            });
        },
    });

    publicWidget.registry.websiteSlidesFullscreenPlayer.include({
        selector: '.o_wslides_fs_main',
        xmlDependencies: ['/e_learning_custom/static/src/xml/website_slides_fullscreen.xml', '/website_slides/static/src/xml/website_slides_share.xml'],
    });

});
