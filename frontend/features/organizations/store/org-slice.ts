import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface OrgState {
  activeOrgId: string | null;
}

const initialState: OrgState = { activeOrgId: null };

const orgSlice = createSlice({
  name: 'org',
  initialState,
  reducers: {
    setActiveOrg: (state, action: PayloadAction<string>) => {
      state.activeOrgId = action.payload;
    },
    clearActiveOrg: (state) => {
      state.activeOrgId = null;
    },
  },
});

export const { setActiveOrg, clearActiveOrg } = orgSlice.actions;
export default orgSlice.reducer;
