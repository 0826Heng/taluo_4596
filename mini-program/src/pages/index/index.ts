import { COPY } from "../../constants/copy";
import { ROUTES, navigateTo } from "../../utils/router";

Page({
  data: {
    todayInspiration: COPY.home.todayInspiration,
    chooseSpread: COPY.home.chooseSpread,
    startPresentation: COPY.home.startPresentation,
    goHistory: COPY.home.goHistory,
  },

  onChooseSpread() {
    navigateTo(ROUTES.spreadPicker);
  },

  onStartToday() {
    navigateTo(ROUTES.reading);
  },

  onGoHistory() {
    navigateTo(ROUTES.history);
  },
});

